import sys
if ".." not in sys.path: sys.path.append("..")
from base_cmd import CmdBase
import wx
import random

class CmdInsertComment(CmdBase):
    """ Insert node """

    def execute(self):
        """ insert comment node """
        self.context.umlwin.CmdInsertNewComment()
            
    def undo(self):  # override
        """ undo insert new comment """
        # not implemented


class CmdInsertOrEditNode(CmdBase):
    def DisplayDialogUmlNodeEdit(self, id, attrs, methods):
        """
        id, attrs, methods are lists of strings
        returns id, attrs, methods as lists of strings
        """
        from dialogs.DialogUmlNodeEdit import DialogUmlNodeEdit
        class EditDialog(DialogUmlNodeEdit):
            def OnClassNameEnter( self, event ):
                self.EndModal(wx.ID_OK) 
        dialog = EditDialog(None)

        dialog.txtClassName.Value, dialog.txtAttrs.Value, dialog.txtMethods.Value = id, "\n".join(attrs), "\n".join(methods)
        if dialog.ShowModal() == wx.ID_OK:
            #wx.MessageBox("got wx.ID_OK")
            result = True
            id = dialog.txtClassName.Value

            def string_to_list_smart(s):
                s = s.strip()
                if s == "":
                    return []
                else:
                    return s.split('\n')

            attrs = string_to_list_smart(dialog.txtAttrs.Value)
            methods = string_to_list_smart(dialog.txtMethods.Value)
            print id, attrs, methods
        else:
            result, id, attrs, methods = False, None, None, None
        dialog.Destroy()
        return (result, id, attrs, methods)


class CmdInsertNewNode(CmdInsertOrEditNode):
    """ Insert new node """

    #def __init__(self, umlwin, wxapp, umlworkspace):
    #    """ pass in all the relevant context """
    #    super(CmdInsertNewNode, self).__init__(umlwin)
    #    self.wxapp = wxapp
    #    self.umlworkspace = umlworkspace

    def execute(self):
        """ insert the new node and refresh the ascii tab too """
        umlwin = self.context.umlwin
        wxapp = self.context.wxapp
        model = self.context.model
        
        #self.umlwin.CmdInsertNewNode()
        
        result, id, attrs, methods = self.DisplayDialogUmlNodeEdit(id='D' + str(random.randint(1,99)),
                                            attrs=['attribute 1', 'attribute 2', 'attribute 3'],
                                            methods=['method A', 'method B', 'method C', 'method D'])

        if result:
            # Ensure unique name
            while model.graph.FindNodeById(id):
                id += '2'

            node = model.AddUmlNode(id, attrs, methods)
            shape = umlwin.CreateUmlShape(node)
            model.classnametoshape[node.id] = shape  # Record the name to shape map so that we can wire up the links later.
            
            node.shape.Show(True)
            
            #self.umlwin.stateofthenation() # if want simple refresh
            #self.umlwin.stage2() # if want overlap removal
            umlwin.stage2(force_stateofthenation=True) # if want overlap removal and proper refresh
            
            umlwin.SelectNodeNow(node.shape)        
        
            wxapp.RefreshAsciiUmlTab()

    def undo(self):  # override
        """ undo insert new node """
        # not implemented


class CmdEditClass(CmdInsertOrEditNode):
    """ Edit node properties """

    def __init__(self, context, shape):
        """ pass in all the relevant context
            as well as the shape/class
        """
        super(CmdEditClass, self).__init__(context)
        self.shape = shape

    def execute(self):
        """  """
        umlwin = self.context.umlwin
        wxapp = self.context.wxapp
        model = self.context.model
        shape = self.shape

        node = shape.node
         
        result, id, attrs, methods = self.DisplayDialogUmlNodeEdit(node.id, node.attrs, node.meths)
        if result:
            model.graph.RenameNode(node, id)   # need special rename cos of underlying graph plumbing - perhaps put setter on id?
            node.attrs = attrs
            node.meths = methods
    
            #umlwin.CmdZapShape(self.shape, deleteNodeToo=False)  # TODO turn this into a sub command
            model.decouple_node_from_shape(shape)
            
            shape = umlwin.CreateUmlShape(node)
            model.classnametoshape[node.id] = shape  # Record the name to shape map so that we can wire up the links later.
    
            # TODO Hmmm - how does new shape get hooked up if the line mapping uses old name!??  Cos of graph's edge info perhaps?
            for edge in model.graph.edges:
                umlwin.CreateUmlEdge(edge)
                
            node.shape.Show(True)
            umlwin.stateofthenation()

            # TODO Why doesn't this select the node?
            #self.SelectNodeNow(node.shape)
            #self.stateofthenation()

    def undo(self):  # override
        """ undo insert new node """
        # not implemented


class CmdInsertImage(CmdBase):
    """ Insert image """

    #def __init__(self, umlwin, frame, config):
    #    """ pass in all the relevant context """
    #    super(CmdInsertImage, self).__init__(umlwin)
    #    self.config = config
    #    self.frame = frame

    def execute(self):
        """ Docstring """
        frame = self.context.frame
        config = self.context.config

        filename = None
        
        thisdir = config.get('LastDirInsertImage', '.') # remember dir path
        dlg = wx.FileDialog(parent=frame, message="choose", defaultDir=thisdir,
            defaultFile="", wildcard="*.jpg", style=wx.OPEN, pos=wx.DefaultPosition)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

            config['LastDirInsertImage'] = dlg.GetDirectory()  # remember dir path
            config.write()
        dlg.Destroy()
        
        self.context.umlwin.CmdInsertNewImageNode(filename)
            
    def undo(self):  # override
        """ Docstring """
        # not implemented
        

