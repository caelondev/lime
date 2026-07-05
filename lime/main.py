from Lexer import Lexer
from Parser import Parser
from AST import Program
import json

LEXER_DEBUG: bool = False
PARSER_DEBUG: bool = True


def main():
    with open("tests/parser.lime", "r") as f:
        code: str = f.read()

    if LEXER_DEBUG:
        print("========== LEXER_DEBUG ==========")
        debug_lex: Lexer = Lexer(source=code)
        while debug_lex.cur_char is not None:
            print(debug_lex.next_token())

    lex = Lexer(source=code)
    parser = Parser(lex)

    if PARSER_DEBUG:
        print("========== PARSER_DEBUG ==========")
        p: Program = parser.parse_program()

        with open("debug/ast.json", "w") as f:
            json.dump(p.json(), f, indent=4)

        print("Dumped AST to ast.json successfully")


if __name__ == "__main__":
    main()
