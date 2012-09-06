import ast

from parsing.core_parser_ast import convert_ast_to_old_parser
from common.logwriter import LogWriterNull

def old_parser(filename):
    from generate_code.gen_asciiart import PySourceAsText
    
    p = PySourceAsText()
    p.Parse(filename)
    return p, ''

def new_parser(filename, log=None):
    if not log:
        log = LogWriterNull()
        
    def ast_parser(filename):
        with open(filename,'r') as f:
            source = f.read()
        
        node = ast.parse(source)
        #print ast.dump(node)
        return node

    node = ast_parser(filename)
    model, debuginfo = convert_ast_to_old_parser(node, filename, log)
    return model, debuginfo
