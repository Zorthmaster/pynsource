#from cmds import *
import cmds.deletion
import cmds.insertion
import cmds.selection
import cmds.diagnostics
import cmds.filemgmt

class Controller():
    def __init__(self, app):
        self.app = app

    def run(self, cmd):
        self.app.cmd_mgr.run(cmd)
        
    def run2(self, cmd_class):
        cmd = cmd_class(self.app.context)
        self.app.cmd_mgr.run(cmd)
        
    # Events from wxapp (for now)

    def CMD_NODE_DELETE_SELECTED(self):
        self.run2(cmds.deletion.CmdNodeDeleteSelected)

    def CMD_NODE_DELETE(self, shape):
        self.run(cmds.deletion.CmdNodeDelete(self.app.context, shape))

    def CMD_INSERT_COMMENT(self):
        self.run2(cmds.insertion.CmdInsertComment)

    def CMD_INSERT_IMAGE(self):
        self.run2(cmds.insertion.CmdInsertImage)

    def CMD_INSERT_CLASS(self):
        self.run2(cmds.insertion.CmdInsertNewNode)

    def CMD_EDIT_CLASS(self, shape):
        self.run(cmds.insertion.CmdEditClass(self.app.context, shape))

    def CMD_DESELECT_ALL_SHAPES(self):
        self.run2(cmds.selection.CmdDeselectAllShapes)
    
    def CMD_DUMP_UML_WORKSPACE(self):
        self.run2(cmds.diagnostics.CmdDumpUmlWorkspace)

    def CMD_FILE_IMPORT_SOURCE(self, files=None, path=None):
        self.run(cmds.filemgmt.CmdFileImportSource(self.app.context, files, path))
    
    def CMD_SAVE_WORKSPACE(self):
        self.run2(cmds.filemgmt.CmdFileSaveWorkspace)

    def CMD_SAVE_WORKSPACE_TO_CONSOLE(self):
        self.run2(cmds.filemgmt.CmdFileSaveWorkspaceToConsole)

    def CMD_FILE_NEW(self):
        self.run2(cmds.filemgmt.CmdFileNew)

    def CMD_LOAD_WORKSPACE_VIA_QUICK_PROMPT(self):
        self.run2(cmds.filemgmt.CmdFileLoadWorkspaceFromQuickPrompt)

    def CMD_LOAD_WORKSPACE_VIA_DIALOG(self):
        self.run2(cmds.filemgmt.CmdFileLoadWorkspaceViaDialog)

    def CMD_LOAD_WORKSPACE_FROM_FILEPATH(self, filepath):
        self.run(cmds.filemgmt.CmdFileLoadWorkspaceFromFilepath(self.app.context, filepath))
    


    """
    # Events from Gui
    

    def CMD_ADD_THING(self, info):
        thing = self.model.AddThing(info)

    def CMD_ADD_INFO_TO_THING(self, thing, moreinfo):
        #thing.AddInfo(moreinfo)
        self.model.AddInfoToThing(thing, moreinfo)

    def CMD_DELETE_THING(self, thing):
        self.model.DeleteThing(thing)
        
    # Other events
    
    def MODEL_THING_ADDED(self, thing, modelsize):
        print "App observer got notified, added value %(thing)s - modelsize now %(modelsize)d" % vars()

    # Methods that adapters need, which require immediate response vs.
    # using the multicasting / eventing approach.  Typically these are
    # called by the server layer which needs to block and build a reponse there and then.

    def CmdGetThingsAsDict(self):
        things = []
        for thing in self.model.things:
            thing_json = thing.to_dict()
            thing_json["link"] = "%s/things/%d" % (self.app.url_server, thing.id)
            things.append(thing_json)
        return {"things": things}
    
    def CmdGetThingAsDict(self, id):
        thing = self.model.FindThing(int(id))
        if thing:
            return thing.to_dict()
        return "Thing id %(id)s not found" % vars()

    def CmdAddThing(self, info):
        try:
            self.app.MainThreadMutexGuiEnter()
            thing = self.model.AddThing(info) # will typically indirectly update a gui
            if thing:
                return thing.to_dict()
            return "Couldn't create thing with info %(info)s" % vars()
        finally:
            self.app.MainThreadMutexGuiLeave()

    def CmdModifyThing(self, id, info):
        try:
            self.app.MainThreadMutexGuiEnter()
            thing = self.model.FindThing(int(id))
            if thing:
                self.model.AddInfoToThing(thing, info)
                return thing.to_dict()
            return "Thing id %(id)s not found" % vars()
        finally:
            self.app.MainThreadMutexGuiLeave()

    def CmdDeleteThing(self, id):
        try:
            self.app.MainThreadMutexGuiEnter()
            thing = self.model.FindThing(int(id))
            if thing:
                self.model.DeleteThing(thing)
                return "ok deleted"
            return "Thing id %(id)s not found" % vars()
        finally:
            self.app.MainThreadMutexGuiLeave()
    """

    """
    Used to redirect via app - lets not do this as too indirect.
    let server see app.controller  !!
    """
    #def CmdGetThingsAsDict(self):
    #    return self.controller.CmdGetThingsAsJson()
    #
    #def CmdGetThingAsDict(self, id):
    #    return self.controller.CmdGetThingAsJson(id)

        