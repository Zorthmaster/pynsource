# Uml canvas

if __name__ == '__main__':
    import sys
    if ".." not in sys.path: sys.path.append("..")

import random

from generate_code.gen_java import PySourceAsJava

from model.umlworkspace import UmlWorkspace

from uml_shapes import *
from coord_utils import setpos, getpos, Move2, percent_change

from layout.layout_basic import LayoutBasic

from layout.snapshots import GraphSnapshotMgr
from layout.layout_spring import GraphLayoutSpring
from layout.overlap_removal import OverlapRemoval
from layout.coordinate_mapper import CoordinateMapper

import wx
import wx.lib.ogl as ogl

from uml_shape_handler import UmlShapeHandler

from architecture_support import *

ogl.Shape.Move2 = Move2

class UmlCanvas(ogl.ShapeCanvas):
    scrollStepX = 10
    scrollStepY = 10
    classnametoshape = {}

    def __init__(self, parent, log, frame):
        ogl.ShapeCanvas.__init__(self, parent)
        maxWidth  = 1000
        maxHeight = 1000
        #self.SetScrollbars(20, 20, maxWidth/20, maxHeight/20)
        self.SetScrollbars(1, 1, 1000, 1000)
        #self.SetVirtualSizeHints(50,50,2000,2000)
        
        self.observers = multicast()
        self.app = None  # assigned later by app boot
        
        self.log = log
        self.frame = frame
        self.SetBackgroundColour("LIGHT BLUE") #wxWHITE)

        self.SetDiagram(ogl.Diagram())
        self.GetDiagram().SetCanvas(self)
        self.save_gdi = []
        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)

        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheelZoom)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
        self.Bind(wx.EVT_CHAR, self.onKeyChar)
        self.working = False

        self.font1 = wx.Font(14, wx.MODERN, wx.NORMAL, wx.NORMAL, False)
        self.font2 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False)

        self._kill_layout = False   # flag to communicate with layout engine.  aborting keypress in gui should set this to true
        self.mark()
        
        @property
        def kill_layout(self):
          return self._kill_layout
        @kill_layout.setter
        def kill_layout(self, value):
          self._kill_layout = value

    def canvas_too_small(self):
        MIN_SENSIBLE_CANVAS_SIZE = 200
        width, height = self.GetSize()
        return width < MIN_SENSIBLE_CANVAS_SIZE or height < MIN_SENSIBLE_CANVAS_SIZE
        
    def InitSizeAndObjs(self):
        # Only call this once enclosing frame has been set up, so that get correct world coord dimensions
        
        if self.canvas_too_small():
            assert False, "InitSizeAndObjs() being called too early - please set up enclosing frame size first"
        
        self.umlworkspace = UmlWorkspace()
        self.layout = LayoutBasic(leftmargin=5, topmargin=5, verticalwhitespace=50, horizontalwhitespace=50, maxclassesperline=7)
        self.snapshot_mgr = GraphSnapshotMgr(graph=self.umlworkspace.graph, umlcanvas=self)
        self.coordmapper = CoordinateMapper(self.umlworkspace.graph, self.GetSize())
        self.layouter = GraphLayoutSpring(self.umlworkspace.graph, gui=self)
        self.overlap_remover = OverlapRemoval(self.umlworkspace.graph, margin=50, gui=self)
        
    def AllToLayoutCoords(self):
        self.coordmapper.AllToLayoutCoords()

    def AllToWorldCoords(self):
        self.coordmapper.AllToWorldCoords()

    def onKeyPress(self, event):
        keycode = event.GetKeyCode()  # http://www.wxpython.org/docs/api/wx.KeyEvent-class.html

        if self.working:
            event.Skip()
            return
        self.working = True

        if keycode == wx.WXK_ESCAPE:
            print "ESC key detected: Abort Layout"
            self.kill_layout = True
        
        if keycode == wx.WXK_RIGHT:
            self.app.run.CmdLayoutExpand(remap_world_to_layout=event.ShiftDown(), remove_overlaps=not event.ControlDown())
            
        elif keycode == wx.WXK_LEFT:
            self.app.run.CmdLayoutContract(remap_world_to_layout=event.ShiftDown(), remove_overlaps=not event.ControlDown())

        elif keycode == wx.WXK_INSERT:
            self.CmdInsertNewNode()
        elif keycode == wx.WXK_DELETE:
            self.app.run.CmdNodeDeleteSelected()
            
        self.working = False
        event.Skip()


    def onKeyChar(self, event):
        if event.GetKeyCode() >= 256:
            event.Skip()
            return
        if self.working:
            event.Skip()
            return
        self.working = True
        
        keycode = chr(event.GetKeyCode())

        if keycode == 'q':
            self.NewEdgeMarkFrom()

        elif keycode == 'w':
            self.NewEdgeMarkTo()
            
        elif keycode in ['1','2','3','4','5','6','7','8']:
            todisplay = ord(keycode) - ord('1')
            self.snapshot_mgr.Restore(todisplay)

        elif keycode in ['b', 'B']:
            self.app.run.CmdDeepLayout()
                
        elif keycode in ['l', 'L']:
            self.app.run.CmdLayout()
            
        elif keycode == 'r':
            self.app.run.CmdRefreshUmlWindow()

        elif keycode == 'R':
            self.Refresh()

        elif keycode in ['d', 'D']:
            self.app.run.CmdDumpUmlWorkspace()

        elif keycode == 's':
            self.resize_virtual_canvas_tofit_bounds(percent_shrinkage_trigger_amount=0)
        
        self.working = False
        event.Skip()


  
    def CmdRememberLayout1(self):
        self.snapshot_mgr.QuickSave(slot=1)
    def CmdRememberLayout2(self):
        self.snapshot_mgr.QuickSave(slot=2)
    def CmdRestoreLayout1(self):
        self.snapshot_mgr.QuickRestore(slot=1)
    def CmdRestoreLayout2(self):
        self.snapshot_mgr.QuickRestore(slot=2)

   
    def SelectNodeNow(self, shape):
        canvas = shape.GetCanvas()

        self.app.run.CmdDeselectAllShapes()

        dc = wx.ClientDC(canvas)
        canvas.PrepareDC(dc)
        shape.Select(True, dc)  # could pass None as dc if you don't want to trigger the OnDrawControlPoints(dc) handler immediately - e.g. if you want to do a complete redraw of everything later anyway
        #canvas.Refresh(False)   # t/f or don't use - doesn't seem to make a difference
        
        #self.UpdateStatusBar(shape)  # only available in the shape evt handler (this method used to live there...)

    def delete_shape_view(self, shape):
        # View
        self.app.run.CmdDeselectAllShapes()
        for line in shape.GetLines()[:]:
            line.Delete()
        shape.Delete()

    def Clear(self):
        print "Draw: Clear"
        self.GetDiagram().DeleteAllShapes()

        dc = wx.ClientDC(self)
        self.GetDiagram().Clear(dc)   # only ends up calling dc.Clear() - I wonder if this clears the screen?

        self.save_gdi = []
        
        self.umlworkspace.Clear()

    def NewEdgeMarkFrom(self):
        selected = [s for s in self.GetDiagram().GetShapeList() if s.Selected()]
        if not selected:
            print "Please select a node"
            return
        
        self.new_edge_from = selected[0].node
        print "From", self.new_edge_from.id

    def NewEdgeMarkTo(self):
        selected = [s for s in self.GetDiagram().GetShapeList() if s.Selected()]
        if not selected:
            print "Please select a node"
            return
        
        tonode = selected[0].node
        print "To", tonode.id
        
        if self.new_edge_from == None:
            print "Please set from node first"
            return
        
        if self.new_edge_from.id == tonode.id:
            print "Can't link to self"
            return
        
        if not self.umlworkspace.graph.FindNodeById(self.new_edge_from.id):
            print "From node %s doesn't seem to be in graph anymore!" % self.new_edge_from.id
            return
        
        edge = self.umlworkspace.graph.AddEdge(self.new_edge_from, tonode, weight=None)
        # TODO should also arguably add to umlworkspace's associations_composition or associations_generalisation list (or create a new one for unlabelled associations like the one we are creating here)
        edge['uml_edge_type'] = ''
        #edge['uml_edge_type'] = 'composition'
        self.CreateUmlEdge(edge)
        self.stateofthenation()

              
    def CreateImageShape(self, F):
        #shape = ogl.BitmapShape()
        shape = BitmapShapeResizable()
        img = wx.Image(F, wx.BITMAP_TYPE_ANY)
        
        #adjusted_img = img.AdjustChannels(factor_red = 1., factor_green = 1., factor_blue = 1., factor_alpha = 0.5)
        #adjusted_img = img.Rescale(10,10)
        adjusted_img = img
        
        bmp = wx.BitmapFromImage(adjusted_img)
        shape.SetBitmap(bmp)

        self.GetDiagram().AddShape(shape)
        shape.Show(True)

        evthandler = UmlShapeHandler(self.log, self.frame, self)  # just init the handler with whatever will be convenient for it to know.
        evthandler.SetShape(shape)
        evthandler.SetPreviousHandler(shape.GetEventHandler())
        shape.SetEventHandler(evthandler)
        self.new_evthandler_housekeeping(evthandler)

        setpos(shape, 0, 0)
        #setpos(shape, node.left, node.top)
        #node.width, node.height = shape.GetBoundingBoxMax()
        #node.shape = shape
        #shape.node = node
        return shape
        
    def CreateUmlShape(self, node):

        def newRegion(font, name, textLst, maxWidth, totHeight = 10):
            # Taken from Boa, but put into the canvas class instead of the scrolled window class.
            region = ogl.ShapeRegion()
            
            if len(textLst) == 0:
                return region, maxWidth, 0
                
            dc = wx.ClientDC(self)  # self is the canvas
            dc.SetFont(font)
    
            for text in textLst:
                w, h = dc.GetTextExtent(text)
                if w > maxWidth: maxWidth = w
                totHeight = totHeight + h + 0 # interline padding
    
            region.SetFont(font)
            region.SetText('\n'.join(textLst))
            region.SetName(name)
    
            return region, maxWidth, totHeight

        shape = DividedShape(width=99, height=98, canvas=self)
        maxWidth = 10 # min node width, grows as we update it with text widths
        
        """
        Future: Perhaps be able to show regions or not. Might need to totally
        reconstruct the shape.
        """
        #if not self.showAttributes: classAttrs = [' ']
        #if not self.showMethods: classMeths = [' ']

        # Create each region.  If height returned is 0 this means don't create this region.
        regionName, maxWidth, nameHeight = newRegion(self.font1, 'class_name', [node.classname], maxWidth)
        regionAttribs, maxWidth, attribsHeight = newRegion(self.font2, 'attributes', node.attrs, maxWidth)
        regionMeths, maxWidth, methsHeight = newRegion(self.font2, 'methods', node.meths, maxWidth)

        # Work out total height of shape
        totHeight = nameHeight + attribsHeight + methsHeight

        # Set regions to be a proportion of the total height of shape
        regionName.SetProportions(0.0, 1.0*(nameHeight/float(totHeight)))
        regionAttribs.SetProportions(0.0, 1.0*(attribsHeight/float(totHeight)))
        regionMeths.SetProportions(0.0, 1.0*(methsHeight/float(totHeight)))

        # Add regions to the shape
        shape.AddRegion(regionName)
        if attribsHeight:   # Dont' make a region unless we have to
            shape.AddRegion(regionAttribs)
        if methsHeight:     # Dont' make a region unless we have to
            shape.AddRegion(regionMeths)

        shape.SetSize(maxWidth + 10, totHeight + 10)
        shape.SetCentreResize(False)  # Specify whether the shape is to be resized from the centre (the centre stands still) or from the corner or side being dragged (the other corner or side stands still).

        regionName.SetFormatMode(ogl.FORMAT_CENTRE_HORIZ)
        shape.region1 = regionName  # Andy added, for later external reference to classname from just having the shape instance.
        
        shape.SetDraggable(True, True)
        shape.SetCanvas(self)
        shape.SetPen(wx.BLACK_PEN)   # Controls the color of the border of the shape
        shape.SetBrush(wx.Brush("WHEAT", wx.SOLID))
        setpos(shape, node.left, node.top)
        self.GetDiagram().AddShape(shape) # self.AddShape is ok too, ShapeCanvas's AddShape is delegated back to Diagram's AddShape.  ShapeCanvas-->Diagram
        shape.Show(True)

        evthandler = UmlShapeHandler(self.log, self.frame, self)  # just init the handler with whatever will be convenient for it to know.
        evthandler.SetShape(shape)
        evthandler.SetPreviousHandler(shape.GetEventHandler())
        shape.SetEventHandler(evthandler)
        self.new_evthandler_housekeeping(evthandler)
        
        shape.FlushText()

        # Don't set the node left,top here as the shape needs to conform to the node.
        # On the other hand the node needs to conform to the shape's width,height.
        # ACTUALLY I now do set the pos of the shape, see above,
        # just before the AddShape() call.
        #
        node.width, node.height = shape.GetBoundingBoxMax()  # TODO: Shouldn't this be in node coords not world coords?
        node.shape = shape
        shape.node = node
        return shape

    def createNodeShape(self, node):     # FROM SPRING LAYOUT
        shape = ogl.RectangleShape( node.width, node.height )
        shape.AddText(node.id)
        setpos(shape, node.left, node.top)
        #shape.SetDraggable(True, True)
        self.AddShape( shape )
        node.shape = shape
        shape.node = node
        
        # wire in the event handler for the new shape
        evthandler = UmlShapeHandler(None, self.frame, self)  # just init the handler with whatever will be convenient for it to know.
        evthandler.SetShape(shape)
        evthandler.SetPreviousHandler(shape.GetEventHandler())
        shape.SetEventHandler(evthandler)
        self.new_evthandler_housekeeping(evthandler)

    def createCommentShape(self, node):
        shape = ogl.TextShape( node.width, node.height )
            
        shape.SetCanvas(self)
        shape.SetPen(wx.BLACK_PEN)
        shape.SetBrush(wx.LIGHT_GREY_BRUSH)
        shape.SetBrush(wx.RED_BRUSH)
        for line in node.comment.split('\n'):
            shape.AddText(line)
        
        setpos(shape, node.left, node.top)
        #shape.SetDraggable(True, True)
        self.AddShape( shape )
        node.shape = shape
        shape.node = node
        
        # wire in the event handler for the new shape
        evthandler = UmlShapeHandler(None, self.frame, self)  # just init the handler with whatever will be convenient for it to know.
        evthandler.SetShape(shape)
        evthandler.SetPreviousHandler(shape.GetEventHandler())
        shape.SetEventHandler(evthandler)
        self.new_evthandler_housekeeping(evthandler)

    def new_evthandler_housekeeping(self, evthandler):
        # notify app of this new evthandler so app can
        # assign the evthandler's .app attribute.
        # Or could have just done:
        #   evthandler.app = self.app
        # here.  But we may need observer for other things later.
        self.observers.NOTIFY_EVT_HANDLER_CREATED(evthandler) 
        
    def CreateUmlEdge(self, edge):
        fromShape = edge['source'].shape
        toShape = edge['target'].shape
        
        edge_label = edge.get('uml_edge_type', '')
        if edge_label == 'generalisation':
            arrowtype = ogl.ARROW_ARROW
        elif edge_label == 'composition':
            arrowtype = ogl.ARROW_FILLED_CIRCLE
        else:
            arrowtype = None

        line = ogl.LineShape()
        line.SetCanvas(self)
        line.SetPen(wx.BLACK_PEN)
        line.SetBrush(wx.BLACK_BRUSH)
        if arrowtype:
            line.AddArrow(arrowtype)
        line.MakeLineControlPoints(2)

        fromShape.AddLine(line, toShape)
        self.GetDiagram().AddShape(line)
        line.Show(True)

    def OnWheelZoom(self, event):
        #print "OnWheelZoom"
        if self.working: return
        self.working = True

        SCROLL_AMOUNT = 40
        if not event.ControlDown():
            oldscrollx = self.GetScrollPos(wx.HORIZONTAL)
            oldscrolly = self.GetScrollPos(wx.VERTICAL)
            if event.GetWheelRotation() < 0:
                self.Scroll(oldscrollx, oldscrolly+SCROLL_AMOUNT)
            else:
                self.Scroll(oldscrollx, max(0, oldscrolly-SCROLL_AMOUNT))
        else:
            if event.GetWheelRotation() < 0:
                self.app.run.CmdLayoutContract(remove_overlaps=not event.ShiftDown())
            else:
                self.app.run.CmdLayoutExpand(remove_overlaps=not event.ShiftDown())

        self.working = False

    # UTILITY - called by CmdFileImportSource, CmdFileLoadWorkspaceBase.LoadGraph   
    def build_view(self, translatecoords=True):
        if translatecoords:
            self.AllToWorldCoords()

        # Clear existing visualisation
        for node in self.umlworkspace.graph.nodes:
            if node.shape:
                self.delete_shape_view(node.shape)
                node.shape = None

        # Create fresh visualisation
        for node in self.umlworkspace.graph.nodes:
            assert not node.shape
            shape = self.CreateUmlShape(node)
            self.umlworkspace.classnametoshape[node.id] = shape  # Record the name to shape map so that we can wire up the links later.
            
        for edge in self.umlworkspace.graph.edges:
            self.CreateUmlEdge(edge)


    # UTILITY - called by
    #
    #CmdInsertNewNodeClass, CmdInsertImage, CmdLayoutExpandContractBase, 
    #umlwin.OnWheelZoom_OverlapRemoval_Defunct, 
    #umlwin.layout_and_position_shapes, 
    #UmlShapeHandler.OnEndDragLeft
    #UmlShapeHandler.OnSizingEndDragLeft
    #LayoutBlackboard.LayoutLoopTillNoChange
    #
    def remove_overlaps(self, watch_removals=True):
        """
        Returns T/F if any overlaps found, so caller can decide whether to
        redraw the screen
        """
        self.overlap_remover.RemoveOverlaps(watch_removals=watch_removals)
        return self.overlap_remover.GetStats()['total_overlaps_found'] > 0
   
    # UTILITY - called by everyone!!??
    #
    #CmdFileLoadWorkspaceBase, CmdInsertComment, CmdEditClass
    #CmdLayoutExpandContractBase, 
    #CmdInsertNewNodeClass
    #umlwin.NewEdgeMarkTo
    #umlwin.OnWheelZoom_OverlapRemoval_Defunct
    #LayoutBlackboard.LayoutThenPickBestScale
    #LayoutBlackboard.Experiment1
    #LayoutBlackboard.LayoutLoopTillNoChange
    #LayoutBlackboard.ScaleUpMadly
    #LayoutBlackboard.GetVitalStats  (only if animate is true)
    #OverlapRemoval.RemoveOverlaps   ( refresh gui if self.gui and watch_removals)
    #GraphSnapshotMgr.RestoreGraph
    #
    # these do an overlap removal first before calling here
    #
    #CmdInsertImage
    #umlwin.layout_and_position_shapes, 
    #UmlShapeHandler.OnEndDragLeft
    #UmlShapeHandler.OnSizingEndDragLeft
    #
    # recalibrate = True - called by core spring layout self.gui.stateofthenation()
    #
    # RENAME?: dc_DiagramClearAndRedraw
    #
    def stateofthenation(self, recalibrate=False, auto_resize_canvas=True):
        if recalibrate:  # was stateofthespring
            self.coordmapper.Recalibrate()
            self.AllToWorldCoords()
            
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)

        for node in self.umlworkspace.graph.nodes:
            node.shape.Move2(dc, node.left, node.top, display=False)
        self.Refresh()

        self.Update() # or wx.SafeYield()  # Without this the nodes don't paint during a "L" layout (edges do!?)
                      # You need to be yielding or updating on a regular basis, so that when your OS/window manager sends repaint messages to your app, it can handle them. See http://stackoverflow.com/questions/10825128/wxpython-how-to-force-ui-refresh

        if auto_resize_canvas:
            self.resize_virtual_canvas_tofit_bounds()

    def frame_calibration(self):
        """
        Calibrate model / shape / layout coordinate mapping system to the
        visible physical window client size.
        """
       
        if self.canvas_too_small():
            print "Canvas too small resize thwarted."
            return

        #Tip: Don't calibrate passing self.GetVirtualSize() as a parameter
        #because it seems to spread the layout out too much, plus perhaps its too
        #uncertain a size to be relied upon?
        #
        self.coordmapper.Recalibrate(self.frame.GetClientSize())

        #Tip2: Since the bounds of the shapes area doesn't change when resizing
        #a frame, we don't need to set the virtualsize of the canvas repeatedly.
        #But we do call this routine in case we can shrink the virtual area at
        #least once. Due to percent_shrinkage_trigger_amount being zero, if the
        #virtual canvas is any bigger than the bounds of the shapes - even 1%
        #bigger - then trim the virtual canvas. Normally the tolerance for
        #shrinking has a leeway of 20-40% or so.
        #
        bounds_width, bounds_height = self.GetBoundsAllShapes()
        frame_width, frame_height = self.GetClientSize() # self.frame.GetSize()

        if self.aged_enough():
            self.resize_virtual_canvas_tofit_bounds(percent_shrinkage_trigger_amount=0)
        
        #if frame_width > bounds_width or frame_height > bounds_height:
        #    print "VIRTUAL SIZE artificially Large - skip", frame_width,frame_height
        #else:
        #    self.resize_virtual_canvas_tofit_bounds(percent_shrinkage_trigger_amount=0)

    def aged_enough(self):
        import datetime
        d = datetime.datetime.now() - self.last_resize_time
        #print d.seconds, "since last mark"
        return d.seconds > 5

    def mark(self):
        import datetime
        self.last_resize_time = datetime.datetime.now()
        #print 'mark', self.last_resize_time
        
    # UTILITY - used by CmdLayout and CmdFileImportBase
    def layout_and_position_shapes(self):
        self.frame_calibration()
        self.AllToLayoutCoords()
        self.layouter.layout(keep_current_positions=False, optimise=True)
        self.AllToWorldCoords()
        if self.remove_overlaps():
            self.stateofthenation()

    def resize_virtual_canvas_tofit_bounds(self, percent_shrinkage_trigger_amount=40):
        """
        Trick is to make the canvas virtual size == bounds of all the shapes.
        You change virtual size by calling SetScrollbars()
        
        As you resize the frame, the canvas virtual size stays the same as what
        you set it to using SetScrollbars() - up until the point at which the
        scrollbars exhaust themselves and disappear - which means the that you
        have finally made frame == virtualsize. After which point virtual size
        auto-grows as the frame continues to grow. If you shrink the frame
        again, then virtualsize will reduce until it hits the old original value
        of virtualsize set by SetScrollbars(). If you continue to reduce the
        frame then the scrollbars appear, but the virtualsize remains the same.
        
        ALGORITHM:
        If its a programmatic change of bounds e.g. via stateofthenation:
            set canvas virtualsize to match bounds taking account % leeway when compacting
        elif is_frame_resize i.e. its a call from resize of frame event:
            if frame > bounds then must be in virtualsize autogrow mode and we should not attempt to alter virtualsize
            else: set canvas virtualsize to match bounds, not taking into account any % leeway.

        Note: repeated calls to frame resize shouldn't be a problem because
        canvas virtualsize should == bounds after the first time its done.
        Making frame smaller won't affect bounds or canvas virtualsize. Making
        frame bigger ditto. Making frame bigger than bounds will result in
        nothing happening cos we do nothing in "autogrow mode".
        """
        
        #print "bounds", self.GetBoundsAllShapes()
        #print "canvas.GetVirtualSize()", self.GetVirtualSize()

        #print "canvas.GetSize()", self.GetSize()
        #print "frame.GetVirtualSize()", self.frame.GetVirtualSize()
        #print "frame.GetSize()", self.frame.GetSize()
        #print "frame.GetClientSize()", self.frame.GetClientSize()

        bounds_width, bounds_height = self.GetBoundsAllShapes()
        virt_width, virt_height = self.GetVirtualSize()
        frame_width, frame_height = self.GetClientSize()
        
        """
        Rule: virtual size must be >= bounds
        """
        need_more_virtual_room = bounds_width > virt_width or bounds_height > virt_height
        
        """
        Rule: virtual size must be no more than n% bigger than the bounds else
        virtualsize will be trimmed/compacted down. The purpose of this is to
        relax the rules and not have it so strict - after all it doesn't hurt to
        have a slightly larger workspace - better than a trim workspace
        jumping/flickering around all the time. Plus if you manually drag resize
        the frame it will trim perfectly.
        """
        need_to_compact = (bounds_width < virt_width or bounds_height < virt_height) and \
            (percent_change(bounds_width, virt_width) > percent_shrinkage_trigger_amount or \
             percent_change(bounds_height, virt_height) > percent_shrinkage_trigger_amount)

        if need_more_virtual_room or need_to_compact:
            oldscrollx = self.GetScrollPos(wx.HORIZONTAL)
            oldscrolly = self.GetScrollPos(wx.VERTICAL)

            print "Setting virtual size to %d,%d | need_more_virtual_room %d need_to_compact %d" % \
                (bounds_width, bounds_height, need_more_virtual_room, need_to_compact)

            self.SetScrollbars(1, 1, bounds_width, bounds_height)
            self.mark()

            if oldscrollx < bounds_width and oldscrolly < bounds_height:
                self.Scroll(oldscrollx, oldscrolly)

            #print "bounds now", self.GetBoundsAllShapes()
            #print "canvas.GetVirtualSize()", self.GetVirtualSize()
        
    def GetBoundsAllShapes(self):
        MARGIN_AROUND_ALL_SHAPES_BOUNDS = 20
        maxx = 0
        maxy = 0
        num_shapes = 0
        for shape in self.umlboxshapes:
            num_shapes += 1
            width, height = shape.GetBoundingBoxMax()
            right = shape.GetX() + width/2
            bottom = shape.GetY() + height/2
            maxx = max(right, maxx)
            maxy = max(bottom, maxy)
        return (maxx + MARGIN_AROUND_ALL_SHAPES_BOUNDS, maxy + MARGIN_AROUND_ALL_SHAPES_BOUNDS)

    def get_umlboxshapes(self):
        #return [s for s in self.GetDiagram().GetShapeList() if not isinstance(s, ogl.LineShape)]
        return [s for s in self.GetDiagram().GetShapeList() if isinstance(s, DividedShape)]  # TODO take into account images and other shapes
        
    umlboxshapes = property(get_umlboxshapes)
    
    def OnDestroy(self, evt):
        for shape in self.GetDiagram().GetShapeList():
            if shape.GetParent() == None:
                shape.SetCanvas(None)

    def OnLeftClick(self, x, y, keys):  # Override of ShapeCanvas method
        # keys is a bit list of the following: KEY_SHIFT  KEY_CTRL
        self.app.run.CmdDeselectAllShapes()


