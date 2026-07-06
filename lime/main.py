from Lexer import Lexer
from Parser import Parser
from AST import Program
import json
from time import time

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float

from Compiler import Compiler

LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = False
COMPILER_DEBUG: bool = True
RUN_CODE: bool = True


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

    if RUN_CODE:
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        try:
            llvm_ir_passed = llvm.parse_assembly(str(mod))
            llvm_ir_passed.verify()
        except Exception as e:
            print(e)
            raise

        target_machine = llvm.Target.from_default_triple().create_target_machine()

        pto = llvm.create_pipeline_tuning_options(speed_level=2, size_level=0)
        pto.loop_vectorization = True
        pto.slp_vectorization = True
        pto.loop_unrolling = True

        pb = llvm.create_pass_builder(target_machine, pto)
        mpm = pb.getModulePassManager()

        opt_st = time()
        changed = mpm.run(llvm_ir_passed, pb)
        opt_et = time()

        print(
            f"O2 optimization pass made modifications: {changed}\n"
            f"=== Optimized in {round((opt_et - opt_st) * 1000, 6)} ms ==="
        )
        if COMPILER_DEBUG:
            with open("debug/ir_optimized.ll", "w") as f:
                f.write(str(llvm_ir_passed))

        engine = llvm.create_mcjit_compiler(llvm_ir_passed, target_machine)
        engine.finalize_object()

        entry = engine.get_function_address("main")
        cfunc = CFUNCTYPE(c_int)(entry)

        st = time()
        res = cfunc()
        et = time()

        print(
            f"\nProgram returned: {res}\n=== Executed in {round((et - st) * 1000, 6)} ms ==="
        )


if __name__ == "__main__":
    main()
