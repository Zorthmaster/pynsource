"""
Compare old and new parsing

Old Parser results model structure:
-----------------------------------

model
    .classlist {classname, classentry ...} where classentry is
        .ismodulenotrealclass T/F
        .classdependencytuples [(fromclass, toclass), ...]
        .classesinheritsfrom [class, ...]  # todo should be renamed classinheritsfrom (singular)
        .attrs [attrobj, ...]
                .attrname
                .attrtype []  # todo should be renamed attrtypes plural
                .compositedependencies  # todo (calculated in real time, should precalc)
        .defs [method, ...]
    .modulemethods = [method, ...]]
"""

import ast
import traceback
import difflib
import os

import sys
sys.path.append("../../src")
from architecture_support import whosdaddy, whosgranddaddy
from core_parser import ClassEntry, Attribute
from keywords import pythonbuiltinfunctions

from logwriter import LogWriter

log = None

DEBUGINFO = 1
DEBUGINFO_IMMEDIATE_PRINT = 0
LOG_TO_CONSOLE = 0
STOP_ON_EXCEPTION = 0

def dump_old_structure(pmodel):
    res = ""
    
    # TODO build this into ClassEntry
    def calc_classname(classentry):
        if classentry.name_long:
            return classentry.name_long
        else:
            return classentry.name
        
    # repair old parse models #TODO build this into the old parser so that we don't have to do this
    for classname, classentry in  pmodel.classlist.items():
        classentry.name = classname
    
    for classname, classentry in  sorted(pmodel.classlist.items(), key=lambda kv: calc_classname(kv[1])):
        res += "%s (is module=%s) inherits from %s class dependencies %s\n" % \
                                    (calc_classname(classentry),
                                     classentry.ismodulenotrealclass,
                                     classentry.classesinheritsfrom,
                                     classentry.classdependencytuples)
        for attrobj in classentry.attrs:
            res += "    %-20s (attrtype %s)\n" % (attrobj.attrname,
                                            attrobj.attrtype) # currently skip calc of self._GetCompositeCreatedClassesFor(attrobj.attrname), arguably it should be precalculated and part of the data structure
        for adef in classentry.defs:
            res += "    %s()\n" % adef
    res += "    modulemethods %s\n" % (pmodel.modulemethods)
    return res
    
def old_parser(filename):
    import sys
    sys.path.append("../../src")
    from generate_code.gen_asciiart import PySourceAsText
    
    p = PySourceAsText()
    p.Parse(filename)
    return p

def ast_parser(filename):
    with open(filename,'r') as f:
        source = f.read()
    
    node = ast.parse(source)
    #print ast.dump(node)
    return node



# S
from ast import *

BOOLOP_SYMBOLS = {
    And:        'and',
    Or:         'or'
}

BINOP_SYMBOLS = {
    Add:        '+',
    Sub:        '-',
    Mult:       '*',
    Div:        '/',
    FloorDiv:   '//',
    Mod:        '%',
    LShift:     '<<',
    RShift:     '>>',
    BitOr:      '|',
    BitAnd:     '&',
    BitXor:     '^'
}

CMPOP_SYMBOLS = {
    Eq:         '==',
    Gt:         '>',
    GtE:        '>=',
    In:         'in',
    Is:         'is',
    IsNot:      'is not',
    Lt:         '<',
    LtE:        '<=',
    NotEq:      '!=',
    NotIn:      'not in'
}

UNARYOP_SYMBOLS = {
    Invert:     '~',
    Not:        'not',
    UAdd:       '+',
    USub:       '-'
}

ALL_SYMBOLS = {}
ALL_SYMBOLS.update(BOOLOP_SYMBOLS)
ALL_SYMBOLS.update(BINOP_SYMBOLS)
ALL_SYMBOLS.update(CMPOP_SYMBOLS)
ALL_SYMBOLS.update(UNARYOP_SYMBOLS)



def convert_ast_to_old_parser(node, filename):
    
    class OldParseModel(object):
        def __init__(self):
            self.classlist = {}
            self.modulemethods = []


    class RhsAnalyser:
        """
        Usage:
            is_rhs_reference_to_a_class()
            
        Scenarios:
            ... = Blah()      want name - before first call which is Blah
            ...append(Blah()) want name - before first call which is Blah (remember the append is on the lhs not the rhs)
            
            ... = blah        may be reinterpreted as      = Blah()  if Blah class found - a relaxed rule I admit
            ...append(blah)   may be reinterpreted as append(Blah()) if Blah class found - a relaxed rule I admit
            
            ... = 10          won't get here because no rhs
            ...append(10)     won't get here because no rhs

            new cases just coming in!
            -------------------------
            * rule seems to be get name or if the name has attributes, the
              name's last attr before the first call (if there is a call)
            
            ... = a.Blah()                                      want names's last attr - before first call
            ... = a.blah                                        want names's last attr - no call here 
            self._max_items = CommandManager.MaxListSize        want names's last attr - no call here - no rhs class ref here !!
            
            ... = a.Blah(b.Fred())                              want names's last attr - before first call
            self.flageditor = FlagEditor(gamestatusstate=self)  want name              - before first call

        """

        def __init__(self, visitor):
            self.visitor = visitor
            
            self.rhs = visitor.rhs
            assert len(self.rhs) > 0
            
            self._calc_rhs_ref_to_class()
            
        def is_rhs_reference_to_a_class(self):
            return self._relaxed_is_instance_a_known_class() or self._is_class_creation()

        def _calc_rhs_ref_to_class(self):
            if self.visitor.made_rhs_call:
                self.rhs_ref_to_class = self.rhs[self.visitor.pos_rhs_call_pre_first_bracket]      # want names's last attr - before first call
            else:
                self.rhs_ref_to_class = self.rhs[-1]     # want names's last attr - no call here 
            
        def _relaxed_is_instance_a_known_class(self):
            for c in self.visitor.quick_parse.quick_found_classes:
                if c.lower() == self.rhs_ref_to_class.lower():
                    self.rhs_ref_to_class = c  # transform into proper class name not the instance
                    return True
            return False
            
        def _is_class_creation(self):            
            # Make sure the rhs is a class creation call NOT a function call.
            t = self.rhs_ref_to_class
            return self.visitor.made_rhs_call and \
                t not in pythonbuiltinfunctions and \
                t not in self.visitor.model.modulemethods and \
                t != 'self' # Also avoid case of self being on the rhs and being considered the first rhs token e.g. self.curr.append(" "*self.curr_width)

            
    class Visitor(ast.NodeVisitor):
        
        def __init__(self, quick_parse):
            self.model = OldParseModel()
            self.stack_classes = []
            self.stack_module_functions = [False]
            self.quick_parse = quick_parse
            self.init_lhs_rhs()
            
            self.result = []
            self.indent_with = ' ' * 4
            self.indentation = 0
            self.new_lines = 0

        def init_lhs_rhs(self):
            self.lhs = []
            self.rhs = []
            self.lhs_recording = True
            self.made_rhs_call = False
            self.made_assignment = False
            self.made_append_call = False
            self.pos_rhs_call_pre_first_bracket = None
            
        def record_lhs_rhs(self, s):
            if self.lhs_recording:
                self.lhs.append(s)
                self.write("\nLHS %d %s\n" % (len(self.lhs), self.lhs), mynote=2)
            else:
                self.rhs.append(s)
                self.write("\nRHS %d %s\n" % (len(self.rhs), self.rhs), mynote=2)
        
        def am_inside_module_function(self):
            return self.stack_module_functions[-1]

        def current_class(self):
            # Returns a ClassEntry or None
            if self.stack_classes:
                return self.stack_classes[-1]
            else:
                return None
        
        def pop_a_function_or_method(self):
            if self.current_class():
                self.current_class().stack_functions.pop()
                self.write("  (POP method) %s " % self.current_class().stack_functions, mynote=3)
            else:
                self.stack_module_functions.pop()
                self.write("  (POP module function) %s " % self.stack_module_functions, mynote=3)
                
        def push_a_function_or_method(self):
            if self.current_class():
                self.current_class().stack_functions.append(True)
                self.write("  (PUSH method) %s " % self.current_class().stack_functions, mynote=3)
            else:
                self.stack_module_functions.append(True)
                self.write("  (PUSH module function) %s " % self.stack_module_functions, mynote=3)
                
        def in_class_static_area(self):
            return self.current_class() and not self.current_class().stack_functions[-1]
            
        def in_method_in_class_area(self):
            return self.current_class() and self.current_class().stack_functions[-1]

        def build_class_entry(self, name):
            c = ClassEntry(name)
            self.model.classlist[name] = c
            self.stack_classes.append(c)
            c.name_long = "_".join([str(c) for c in self.stack_classes])
            self.write("  (inside class %s) %s " % (c.name, [str(c) for c in self.stack_classes]), mynote=3)
            return c

        def add_composite_dependency(self, t):
            if t not in self.current_class().classdependencytuples:
                self.current_class().classdependencytuples.append(t)
                
        def flush_state(self, msg=""):
            self.write("""
                <table>
                    <tr>
                        <th>lhs</th>
                        <th>rhs</th>
                        <th>made_assignment</th>
                        <th>made_append_call</th>
                        <th>made_rhs_call</th>
                        <th>pos_rhs_call_pre_first_bracket</th>
                        <th>in_class_static_area</th>
                        <th>in_method_in_class_area</th>
                        <th></th>
                    </tr>
                    <tr>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                    </tr>
                </table>
            """ % (self.lhs, self.rhs,
                    self.made_assignment,
                    self.made_append_call,
                    self.made_rhs_call,
                    self.pos_rhs_call_pre_first_bracket,
                    self.in_class_static_area(),
                    self.in_method_in_class_area(),
                    msg), mynote=0)

        def flush(self):
            self.flush_state(whosgranddaddy())
            
            # At this point we have both lhs and rhs plus three flags and can
            # make a decision about what to create.
        
            def create_attr_static(t):
                self.current_class().AddAttribute(attrname=t, attrtype=['static'])
                return t
            def create_attr(t):
                if (t == '__class__') and len(self.lhs) >= 3:
                    t = self.lhs[2]
                    self.current_class().AddAttribute(attrname=t, attrtype=['static'])
                else:
                    self.current_class().AddAttribute(attrname=t, attrtype=['normal'])
                return t
            def create_attr_many(t):
                self.current_class().AddAttribute(attrname=t, attrtype=['normal', 'many'])
                return t
            def create_attr_please(t):
                if self.made_append_call:
                    t = create_attr_many(t)
                else:
                    t = create_attr(t)
                return t

            if self.made_assignment or self.made_append_call:
                
                if self.in_class_static_area():
                    t = create_attr_static(self.lhs[0])
                elif self.in_method_in_class_area() and self.lhs[0] == 'self':
                    t = create_attr_please(self.lhs[1])
                else:
                    pass # in module area
          
                if self.lhs[0] == 'self' and len(self.rhs) > 0:
                    ra = RhsAnalyser(visitor=self)
                    if ra.is_rhs_reference_to_a_class():
                        self.add_composite_dependency((t, ra.rhs_ref_to_class))
                        
            self.init_lhs_rhs()
            self.flush_state()
            self.write("<hr>", mynote=2)

        
        
        # MAIN VISIT METHODS

        def write(self, x, mynote=0):
            assert(isinstance(x, str))
            if self.new_lines:
                if self.result:
                    self.result.append('\n' * self.new_lines)
                self.result.append(self.indent_with * self.indentation)
                self.new_lines = 0
            x = "<span class=mynote%d>%s</span>" % (mynote,x)
            self.result.append(x)
            if DEBUGINFO_IMMEDIATE_PRINT:
                print x
                
        def newline(self, node=None, extra=0):
            self.new_lines = max(self.new_lines, 1 + extra)

            # A
            self.flush()

        def body(self, statements):
            self.new_line = True
            self.indentation += 1
            for stmt in statements:
                self.visit(stmt)
            self.indentation -= 1

        # S
        def body_or_else(self, node):
            self.body(node.body)
            if node.orelse:
                self.newline()
                self.write('else:')
                self.body(node.orelse)

        # S
        def signature(self, node):
            want_comma = []
            def write_comma():
                if want_comma:
                    self.write(', ')
                else:
                    want_comma.append(True)
    
            padding = [None] * (len(node.args) - len(node.defaults))
            for arg, default in zip(node.args, padding + node.defaults):
                write_comma()
                self.visit(arg)
                if default is not None:
                    self.write('=')
                    self.visit(default)
            if node.vararg is not None:
                write_comma()
                self.write('*' + node.vararg)
            if node.kwarg is not None:
                write_comma()
                self.write('**' + node.kwarg)
    
        # S
        def decorators(self, node):
            for decorator in node.decorator_list:
                self.newline(decorator)
                self.write('@')
                self.visit(decorator)
    
        # Statements

        def visit_Assign(self, node):  # seems to be the top of the name / attr / chain
            self.write("\nvisit_Assign ", mynote=1)
            self.newline(node)
            
            for idx, target in enumerate(node.targets):
                if idx:
                    self.write(', ')
                self.visit(target)

            self.write(' = ')
            
            # A
            self.lhs_recording = False  # are parsing the rhs now
            
            self.visit(node.value)  # node.value is an ast obj, can't print it
            
            # A
            self.made_assignment = True

        # S            
        def visit_AugAssign(self, node):
            self.newline(node)
            self.visit(node.target)
            self.write(' '+BINOP_SYMBOLS[type(node.op)] + '= ')
            self.visit(node.value)
    
        # S            
        def visit_ImportFrom(self, node):
            self.newline(node)
            self.write('from %s%s import ' % ('.' * node.level, node.module))
            for idx, item in enumerate(node.names):
                if idx:
                    self.write(', ')
                self.visit(item)
    
        # S            
        def visit_Import(self, node):
            self.newline(node)
            for item in node.names:
                self.write('import ')
                self.visit(item)

        def visit_Expr(self, node):
            #self.write("visit_Expr")
            self.newline(node)
            self.generic_visit(node)
            
        def visit_FunctionDef(self, node):
            self.newline(extra=1)
            self.newline(node)
            self.write("\nvisit_FunctionDef\n", mynote=1)
            self.write('def %s(' % node.name)
            
            # A
            if not self.current_class() and not self.am_inside_module_function():
                self.model.modulemethods.append(node.name)
                assert node.name in self.quick_parse.quick_found_module_defs
            elif self.current_class():
                self.current_class().defs.append(node.name)

            # A
            self.push_a_function_or_method()
            
            self.write('):')
            self.body(node.body)
            
            # A
            self.flush()
            self.pop_a_function_or_method()
            
        def visit_ClassDef(self, node):
            self.newline(extra=2)
            #self.decorators(node)
            self.newline(node)
            
            self.write("\nvisit_ClassDef\n", mynote=1)
            self.write('class %s' % node.name)
            
            # A
            c = self.build_class_entry(node.name)

            for base in node.bases:
                self.visit(base)

                # A
                c.classesinheritsfrom.append(".".join(self.lhs))
            
            self.body(node.body)

            # A
            self.flush()
            self.stack_classes.pop()
            self.write("  (pop a class) stack now: %s " % [str(c) for c in self.stack_classes], mynote=3)

            
        # S            
        def visit_If(self, node):
            self.newline(node)
            self.write('if ')
            self.visit(node.test)
            self.write(':')
            self.body(node.body)
            while True:
                else_ = node.orelse
                if len(else_) == 1 and isinstance(else_[0], If):
                    node = else_[0]
                    self.newline()
                    self.write('elif ')
                    self.visit(node.test)
                    self.write(':')
                    self.body(node.body)
                else:
                    if len(else_) > 0:
                        self.newline()
                        self.write('else:')
                        self.body(else_)
                    break
    
        # S            
        def visit_For(self, node):
            self.newline(node)
            self.write('for ')
            self.visit(node.target)
            self.write(' in ')
            self.visit(node.iter)
            self.write(':')
            self.body_or_else(node)
    
        # S            
        def visit_While(self, node):
            self.newline(node)
            self.write('while ')
            self.visit(node.test)
            self.write(':')
            self.body_or_else(node)
    
        # S            
        def visit_With(self, node):
            self.newline(node)
            self.write('with ')
            self.visit(node.context_expr)
            if node.optional_vars is not None:
                self.write(' as ')
                self.visit(node.optional_vars)
            self.write(':')
            self.body(node.body)
    
        # S            
        def visit_Pass(self, node):
            self.newline(node)
            self.write('pass')
    
        # S            
        def visit_Print(self, node):
            # XXX: python 2.6 only
            self.newline(node)
            self.write('print ')
            want_comma = False
            if node.dest is not None:
                self.write(' >> ')
                self.visit(node.dest)
                want_comma = True
            for value in node.values:
                if want_comma:
                    self.write(', ')
                self.visit(value)
                want_comma = True
            if not node.nl:
                self.write(',')
    
        # S            
        def visit_Delete(self, node):
            self.newline(node)
            self.write('del ')
            for idx, target in enumerate(node.targets):
                if idx:
                    self.write(', ')
                self.visit(target)
    
        # S            
        def visit_TryExcept(self, node):
            self.newline(node)
            self.write('try:')
            self.body(node.body)
            for handler in node.handlers:
                self.visit(handler)
    
        # S            
        def visit_TryFinally(self, node):
            self.newline(node)
            self.write('try:')
            self.body(node.body)
            self.newline(node)
            self.write('finally:')
            self.body(node.finalbody)
    
        # S            
        def visit_Global(self, node):
            self.newline(node)
            self.write('global ' + ', '.join(node.names))
    
        # S            
        def visit_Nonlocal(self, node):
            self.newline(node)
            self.write('nonlocal ' + ', '.join(node.names))
    
        # S            
        def visit_Return(self, node):
            self.newline(node)
            if node.value is not None:
                self.write('return ')
                self.visit(node.value)
            else:
                self.write('return')
    
        # S            
        def visit_Break(self, node):
            self.newline(node)
            self.write('break')
    
        # S            
        def visit_Continue(self, node):
            self.newline(node)
            self.write('continue')
    
        # S            
        def visit_Raise(self, node):
            # XXX: Python 2.6 / 3.0 compatibility
            self.newline(node)
            self.write('raise')
            if hasattr(node, 'exc') and node.exc is not None:
                self.write(' ')
                self.visit(node.exc)
                if node.cause is not None:
                    self.write(' from ')
                    self.visit(node.cause)
            elif hasattr(node, 'type') and node.type is not None:
                self.visit(node.type)
                if node.inst is not None:
                    self.write(', ')
                    self.visit(node.inst)
                if node.tback is not None:
                    self.write(', ')
                    self.visit(node.tback)
    
        # Expressions

        def visit_Attribute(self, node):
            self.visit(node.value)
            
            # A
            self.write("\nvisit_Attribute %s\n" % node.attr, mynote=1)
            self.record_lhs_rhs(node.attr)
            
            self.write('.' + node.attr)

        def visit_Call(self, node):
            self.visit(node.func)
            self.write("\nvisit_Call %s" % self.rhs, mynote=1)

            # A
            just_now_made_append_call = self.detect_append_call()
                
            self.write('(')
            for arg in node.args:
                #write_comma()
                self.visit(arg)
            for keyword in node.keywords:
                #write_comma()
                self.write(keyword.arg + '=')
                self.visit(keyword.value)
            if node.starargs is not None:
                #write_comma()
                self.write('*')
                self.visit(node.starargs)
            if node.kwargs is not None:
                #write_comma()
                self.write('**')
                self.visit(node.kwargs)
            self.write(')')

            # A
            # Ensure self.made_append_call and self.made_rhs_call are different things.
            #
            # An append call does not necessarily imply a rhs call was made.
            # e.g. .append(blah) or .append(10) are NOT a calls on the rhs, in
            # fact there is no rhs clearly defined yet except till inside the
            # append(... despite it superficially looking like a function call
            #               
            if len(self.rhs) > 0 and not just_now_made_append_call:
                if not self.made_rhs_call:
                    self.pos_rhs_call_pre_first_bracket = len(self.rhs)-2  # remember which is the token before the first bracket
                self.made_rhs_call = True
               
        # A
        def detect_append_call(self):
            just_now_made_append_call = False
            if len(self.lhs) == 3 and \
                    self.in_method_in_class_area() and \
                    self.lhs[0] == 'self' and \
                    self.lhs[2] in ('append', 'add', 'insert') and \
                    not self.rhs:
                self.lhs_recording = False # start recording tokens (names, attrs) on rhs
                self.made_append_call = just_now_made_append_call = True
                self.write("\n just_now_made_append_call", mynote=1)
            return just_now_made_append_call
            
        def visit_Name(self, node):
            self.write("\nvisit_Name %s\n" % node.id, mynote=1)
            self.write(node.id)

            # A
            self.record_lhs_rhs(node.id)

        def visit_Str(self, node):
            self.write(repr(node.s))

        # S
        def visit_Bytes(self, node):
            self.write(repr(node.s))

        def visit_Num(self, node):
            self.write(repr(node.n))

        # S
        def visit_Tuple(self, node):
            self.write('(')
            idx = -1
            for idx, item in enumerate(node.elts):
                if idx:
                    self.write(', ')
                self.visit(item)
            self.write(idx and ')' or ',)')
    
        # S
        def sequence_visit(left, right):
            def visit(self, node):
                self.write(left)
                for idx, item in enumerate(node.elts):
                    if idx:
                        self.write(', ')
                    self.visit(item)
                self.write(right)
            return visit
    
        # S
        visit_List = sequence_visit('[', ']')
        visit_Set = sequence_visit('{', '}')
        del sequence_visit
    
        # S
        def visit_Dict(self, node):
            self.write('{')
            for idx, (key, value) in enumerate(zip(node.keys, node.values)):
                if idx:
                    self.write(', ')
                self.visit(key)
                self.write(': ')
                self.visit(value)
            self.write('}')
    
        # S
        def visit_BinOp(self, node):
            self.visit(node.left)
            self.write(' %s ' % BINOP_SYMBOLS[type(node.op)])
            self.visit(node.right)
    
        # S
        def visit_BoolOp(self, node):
            self.write('(')
            for idx, value in enumerate(node.values):
                if idx:
                    self.write(' %s ' % BOOLOP_SYMBOLS[type(node.op)])
                self.visit(value)
            self.write(')')
    
        # S
        def visit_Compare(self, node):
            self.write('(')
            self.visit(node.left)
            for op, right in zip(node.ops, node.comparators):
                self.write(' %s ' % CMPOP_SYMBOLS[type(op)])
                self.visit(right)
            self.write(')')
    
        # S
        def visit_UnaryOp(self, node):
            self.write('(')
            op = UNARYOP_SYMBOLS[type(node.op)]
            self.write(op)
            if op == 'not':
                self.write(' ')
            self.visit(node.operand)
            self.write(')')
    
        # S
        def visit_Subscript(self, node):
            self.visit(node.value)
            self.write('[')
            self.visit(node.slice)
            self.write(']')
    
        # S
        def visit_Slice(self, node):
            if node.lower is not None:
                self.visit(node.lower)
            self.write(':')
            if node.upper is not None:
                self.visit(node.upper)
            if node.step is not None:
                self.write(':')
                if not (isinstance(node.step, Name) and node.step.id == 'None'):
                    self.visit(node.step)
    
        # S
        def visit_ExtSlice(self, node):
            for idx, item in node.dims:
                if idx:
                    self.write(', ')
                self.visit(item)
    
        # S
        def visit_Yield(self, node):
            self.write('yield ')
            self.visit(node.value)
    
        # S
        def visit_Lambda(self, node):
            self.write('lambda ')
            self.signature(node.args)
            self.write(': ')
            self.visit(node.body)
    
        # S
        def visit_Ellipsis(self, node):
            self.write('Ellipsis')
    
        # S
        def generator_visit(left, right):
            def visit(self, node):
                self.write(left)
                self.visit(node.elt)
                for comprehension in node.generators:
                    self.visit(comprehension)
                self.write(right)
            return visit
    
        # S
        visit_ListComp = generator_visit('[', ']')
        visit_GeneratorExp = generator_visit('(', ')')
        visit_SetComp = generator_visit('{', '}')
        del generator_visit
    
        # S
        def visit_DictComp(self, node):
            self.write('{')
            self.visit(node.key)
            self.write(': ')
            self.visit(node.value)
            for comprehension in node.generators:
                self.visit(comprehension)
            self.write('}')
    
        # S
        def visit_IfExp(self, node):
            self.visit(node.body)
            self.write(' if ')
            self.visit(node.test)
            self.write(' else ')
            self.visit(node.orelse)
    
        # S
        def visit_Starred(self, node):
            self.write('*')
            self.visit(node.value)
    
        # S
        def visit_Repr(self, node):
            # XXX: python 2.6 only
            self.write('`')
            self.visit(node.value)
            self.write('`')
    
        # Helper Nodes
    
        # S
        def visit_alias(self, node):
            self.write(node.name)
            if node.asname is not None:
                self.write(' as ' + node.asname)
    
        # S
        def visit_comprehension(self, node):
            self.write(' for ')
            self.visit(node.target)
            self.write(' in ')
            self.visit(node.iter)
            if node.ifs:
                for if_ in node.ifs:
                    self.write(' if ')
                    self.visit(if_)
    
        # S
        def visit_ExceptHandler(self, node):
            self.newline(node)
            self.write('except')
            if node.type is not None:
                self.write(' ')
                self.visit(node.type)
                if node.name is not None:
                    self.write(' as ')
                    self.visit(node.name)
            self.write(':')
            self.body(node.body)

        # Note
        # S means this code is uneccesary for 99% of extraction of info I want.  I only put it in to stop some errors re huge accumulating rhs
        # A means Andy's extra bits of code
        
    
    class QuickParse(object):
        def __init__(self, filename):
            import re   
            # secret regular expression based preliminary scan for classes and module defs
            # Feed the file text into findall(); it returns a list of all the found strings
            with open(filename, 'r') as f:
                source = f.read()
            self.quick_found_classes = re.findall(r'^\s*class (.*?)[\(:]', source, re.MULTILINE)  
            self.quick_found_module_defs = re.findall(r'^def (.*)\(.*\):', source, re.MULTILINE)
            self.quick_found_module_attrs = re.findall(r'^(\S.*?)[\.]*.*\s*=.*', source, re.MULTILINE)
            
            log.out_wrap_in_html("quick_found_classes %s<br>quick_found_module_defs %s<br>quick_found_module_attrs %s<br>" % \
                                (self.quick_found_classes, self.quick_found_module_defs, self.quick_found_module_attrs),
                                style_class='quick_findings')

    
    qp = QuickParse(filename)

    v = Visitor(qp)
    
    try:
        v.visit(node)
    except Exception as err:
        log.out("Parsing Visit error: {0}".format(err), force_print=True)
        log.out_wrap_in_html(traceback.format_exc(), style_class='stacktrace')
        if STOP_ON_EXCEPTION:
            if DEBUGINFO:
                debuginfo = '<br>'.join(v.result)
                log.out(debuginfo)
                log.out_html_footer()
                log.finish()
            raise

    debuginfo = '<br>'.join(v.result)
    return v.model, debuginfo


#####

def parse_and_convert(in_filename, print_diffs=True):
    global log
    log = LogWriter(in_filename, print_to_console=LOG_TO_CONSOLE)
    
    def oldparse():
        model = old_parser(in_filename)
        d1 = dump_old_structure(model)
        log.out_wrap_in_html(d1, style_class='dump1')
        return d1
        
    def newparse():
        node = ast_parser(in_filename)
        model, debuginfo = convert_ast_to_old_parser(node, in_filename)
        d2 = dump_old_structure(model)
        log.out_wrap_in_html(d2, style_class='dump1')
        return d2, debuginfo

    def dodiff(d1, d2):
        diff = difflib.ndiff(d1.splitlines(1),d2.splitlines(1))
        diff_s = ''.join(diff)
        return diff_s
    
    try:
        log.out_html_header()
        log.out("PARSING: %s *****\n" % in_filename)
        
        d1 = oldparse()
        log.out_divider()
        d2, debuginfo = newparse()
        
        comparedok = (d1 == d2)
        log.out("** old vs new method comparison = %s" % comparedok)

        diff_s = dodiff(d1, d2)
        log.out_wrap_in_html(diff_s, style_class='dumpdiff')
        if not comparedok and print_diffs:
            print diff_s

        if DEBUGINFO:
            log.out(debuginfo)
    
        log.out_html_footer()
    finally:
        log.finish()
        
    return comparedok


############        

RUN_TEST_SUITE = 1

results = []
def reset_tests():
    global results
    results = []
def test(filename):
    results.append(parse_and_convert(filename))
def test_not(filename):
    results.append(not parse_and_convert(filename, print_diffs=False))
def report(msg):
    if all(results):
        print "%s OK" % msg
    else:
        print "oooops %s broken" % msg, results

if RUN_TEST_SUITE:
    reset_tests()    
    test('../../tests/python-in/testmodule01.py')
    test('../../tests/python-in/testmodule02.py')
    test('../../tests/python-in/testmodule03.py')
    test('../../tests/python-in/testmodule04.py')
    test('../../tests/python-in/testmodule05.py') # (inner classes)
    test('../../tests/python-in/testmodule06.py')
    test('../../tests/python-in/testmodule07.py')
    test('../../tests/python-in/testmodule66.py')
    report("official parsing tests")
    
    reset_tests()    
    test('../../src/printframework.py')
    test('../../src/asciiworkspace.py')
    report("subsidiary parsing tests")
    
    # Expect these to fail cos ast parsing is genuinely better
    reset_tests()    
    test_not('../../tests/python-in/testmodule08_multiple_inheritance.py') # ast is better (base classes with .)
    test_not('../../src/pynsource.py') # ast is better (less module methods found - more correct)
    report("ast parsing is genuinely better")

    # Extras
    print

#print parse_and_convert('../../src/pyNsourceGui.py') # different - to investigate
print parse_and_convert('../../src/command_pattern.py') # ast is better, nested module functions ignored. class checked for when relaxed attr ref to instance

"""
TODO

handle properties
    currentItem = property(_get_current_item)
    currentRedoItem = property(_get_current_redo_item)
    maxItems = property(_get_max_items, _set_max_items)
currently appearing as static attrs - which is ok.  Should be normal attra.


"""
