from Lexer import Lexer
from Parser import Parser
from AST import Program
import json

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float

from Compiler import Compiler

LEXER_DEBUG: bool = True
PARSER_DEBUG: bool = True
COMPILER_DEBUG: bool = False


def main():
    with open("tests/compiler.lime", "r") as f:
        code: str = f.read()

    if LEXER_DEBUG:
        print("========== LEXER_DEBUG ==========")
        debug_lex: Lexer = Lexer(source=code)
        while debug_lex.cur_char is not None:
            print(debug_lex.next_token())

    lex = Lexer(source=code)
    parser = Parser(lex)

    p: Program = parser.parse_program()
    if len(parser.errors) > 0:
        for e in parser.errors:
            print(e)
        exit(1)

    if PARSER_DEBUG:
        print("========== PARSER_DEBUG ==========")

        with open("debug/ast.json", "w") as f:
            json.dump(p.json(), f, indent=4)

        print("Dumped AST to ast.json successfully")

    comp = Compiler()

    # output steps
    mod: ir.Module = comp.module
    mod.triple = llvm.get_default_triple()  # architecture

    comp.compile(p)

    if COMPILER_DEBUG:
        with open("debug/ir.ll", "w") as f:
            f.write(str(mod))
        print(f"successfully compiled source '{code}' to LLVM IR")


if __name__ == "__main__":
    main()
