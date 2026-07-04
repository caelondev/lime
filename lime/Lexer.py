from Token import Token, TokenType
from typing import Any


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = -1
        self.read_pos = 0
        self.ln_number = 1
        self.cur_char: str | None = None
        self.__read_char()

    def next_token(self) -> Token:
        self.__skip_whitespace()

        if self.cur_char is None:
            return self.__new_token(TokenType.EOF, None)

        if self.__is_digit(self.cur_char):
            return self.__read_number()

        match self.cur_char:
            case "+":
                tok = self.__new_token(TokenType.PLUS, self.cur_char)
            case "-":
                tok = self.__new_token(TokenType.MINUS, self.cur_char)
            case "*":
                tok = self.__new_token(TokenType.ASTERISK, self.cur_char)
            case "/":
                tok = self.__new_token(TokenType.SLASH, self.cur_char)
            case "^":
                tok = self.__new_token(TokenType.POW, self.cur_char)
            case "%":
                tok = self.__new_token(TokenType.MODULO, self.cur_char)
            case ";":
                tok = self.__new_token(TokenType.SEMICOLON, self.cur_char)
            case "(":
                tok = self.__new_token(TokenType.LEFT_PARENTHESIS, self.cur_char)
            case ")":
                tok = self.__new_token(TokenType.RIGHT_PARENTHESIS, self.cur_char)
            case _:
                tok = self.__new_token(TokenType.ILLEGAL, self.cur_char)

        self.__read_char()
        return tok

    def __read_number(self) -> Token:
        output = ""
        dot_count = 0
        start_pos = self.position

        while self.cur_char is not None and (
            self.__is_digit(self.cur_char) or self.cur_char == "."
        ):
            if self.cur_char == ".":
                dot_count += 1
                if dot_count > 1:
                    return self.__new_token(
                        TokenType.ILLEGAL,
                        self.source[start_pos : self.position + 1],
                    )

            output += self.cur_char
            self.__read_char()

        if dot_count == 0:
            return self.__new_token(TokenType.INT, int(output))

        return self.__new_token(TokenType.FLOAT, float(output))

    def __is_digit(self, ch: str | None) -> bool:
        return ch is not None and "0" <= ch <= "9"

    def __new_token(self, tt: TokenType, lit: Any) -> Token:
        return Token(
            type=tt,
            literal=lit,
            ln_number=self.ln_number,
            pos=self.position,
        )

    def __read_char(self) -> None:
        if self.read_pos >= len(self.source):
            self.cur_char = None
        else:
            self.cur_char = self.source[self.read_pos]

        self.position = self.read_pos
        self.read_pos += 1

    def __skip_whitespace(self) -> None:
        while self.cur_char is not None and self.cur_char in " \t\r\n":
            if self.cur_char == "\n":
                self.ln_number += 1

            self.__read_char()
