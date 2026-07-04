from Lexer import Lexer

LEXER_DEBUG: bool = True


def main():
    with open("tests/lexer.lime", "r") as f:
        code: str = f.read()

    if LEXER_DEBUG:
        debug_lex: Lexer = Lexer(source=code)
        while debug_lex.cur_char is not None:
            print(debug_lex.next_token())


if __name__ == "__main__":
    main()
