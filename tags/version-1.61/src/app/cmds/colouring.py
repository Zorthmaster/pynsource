from base_cmd import CmdBase
import wx
import os
import random
from common.uml_colours import official2

class CmdColourSiblings(CmdBase):
    
    last_offset = 0

    def __init__(self, color_range_offset=False):
        self.color_range_offset = color_range_offset
        
    def execute(self):
        from common.uml_colours import official2
        
        umlwin = self.context.umlwin
        
        if self.color_range_offset:
            #offset = random.randint(1, 10)
            CmdColourSiblings.last_offset += 1
            offset = CmdColourSiblings.last_offset
        else:
            offset = 0

        self.context.model.graph.colour_mark_siblings()
        
        clrs = official2.strip().split('\n')

        dc = wx.ClientDC(umlwin)
        umlwin.PrepareDC(dc)
        for node in self.context.model.graph.nodes:
            clr = clrs[(node.colour_index + offset) % len(clrs)]
            colour=wx.Brush(clr)
            
            node.shape.SetBrush(colour)
            #print "colour_index", node.id, node.colour_index, clr
        umlwin.Redraw(dc)

class CmdCycleColours(CmdBase):
    
    last_index = 0
    
    def __init__(self, colour=None):
        self.colour = colour

    def execute(self):
        from common.uml_colours import official2
        umlwin = self.context.umlwin

        if self.colour == None:
            #colour=wx.WHITE_BRUSH
            
            #from wx.lib.colourdb import getColourList
            #clrs = getColourList()
            
            clrs = official2.strip().split('\n')
            
            CmdCycleColours.last_index += 1
            clr = clrs[CmdCycleColours.last_index%len(clrs)]
            self.context.frame.SetStatusText(clr)
            
            self.colour=wx.Brush(clr)  # colour=wx.Brush(clr, wx.SOLID)
        
        dc = wx.ClientDC(umlwin)
        umlwin.PrepareDC(dc)
        for node in self.context.model.graph.nodes:
            node.shape.SetBrush(self.colour)
        umlwin.Redraw(dc)

class CmdColourSequential(CmdBase):
    def __init__(self, color_range_offset=False):
        self.color_range_offset = color_range_offset
        
    def execute(self):
        from common.uml_colours import official2
        umlwin = self.context.umlwin
        
        if self.color_range_offset:
            offset = random.randint(1, 10)
        else:
            offset = 0

        index = 0 + offset
        index_max = len(official2)
        
        for node in self.context.model.graph.nodes:
            node.colour_index = index
            index += 1
            if index > index_max:
                index = 0

        clrs = official2.strip().split('\n')

        dc = wx.ClientDC(umlwin)
        umlwin.PrepareDC(dc)
        for node in self.context.model.graph.nodes:
            clr = clrs[(node.colour_index + offset) % len(clrs)]
            colour=wx.Brush(clr)
            node.shape.SetBrush(colour)
            #print "colour_index", node.id, node.colour_index, clr
        umlwin.Redraw(dc)

class CmdBuildColourChartWorkspace(CmdBase):
    def execute(self):

        umlcanvas = self.context.umlwin
        umlcanvas.Clear()
        
        graph = self.context.model.graph
        
        clrs = official2.strip().split('\n')
        
        NODE_HEIGHT = 30
        MAX_Y_NODES = 18 
        index = 0
        x = y = 10
        for clr in clrs:
            #print clr
            node = graph.NotifyCreateNewNode("%d %s" % (index, clr), x, y, 100, NODE_HEIGHT)
            graph.AddNode(node)
            index += 1
            y += NODE_HEIGHT + 5
            if index%MAX_Y_NODES == 0:
                y = 10
                x += 280
       
        # build view from model
        umlcanvas.build_view(translatecoords=False)

        # set layout coords to be in sync with world, so that if expand scale things will work
        umlcanvas.coordmapper.Recalibrate()
        umlcanvas.AllToLayoutCoords()
        
        # refresh view
        umlcanvas.GetDiagram().ShowAll(1) # need this, yes
        umlcanvas.stateofthenation()
        
        self.context.wxapp.set_app_title("(Untitled)")
        umlcanvas.CmdTrimScrollbars()

        self.context.wxapp.app.run.CmdColourSequential()

            