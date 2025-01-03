from abc import ABC
from enum import Enum, auto
from typing import Generic, TypeVar


class PrimitiveTypes(Enum):
    STR = "Str"
    INT = "Int"
    FLOAT = "Float"
    UNIT = "()"
    LIST = "List"


class TT(Enum):
    COLON = ":"
    COMMA = ","
    BACKSLASH = "\\"
    FUNCTION_ARROW = "→"
    PLUS = "+"
    # minus!
    DASH = "-"
    DOUBLE_COLON = "::"
    OPEN_PAREN = "("
    CLOSE_PAREN = ")"
    OPEN_SQUARE = "["
    UNDERSCORE = "_"
    GREATER_THAN = ">"
    LESS_THAN = ">"
    CURLY_OPEN = "{"
    CURLY_CLOSE = "}"
    EQ = "="
    PIPE = "|"
    CLOSE_SQUARE = "]"
    IDENT = "IDENT"
    LITERAL = "LITERAL"
    COMMENT = "COMMENT"
    PRIME_FORM = "PRIME_FORM"
    DUMMY = "DUMMY"


SYMBOLS = [TT.EQ, TT.LESS_THAN, TT.GREATER_THAN, TT.DASH, TT.FUNCTION_ARROW]

operators = {
    "+": {
        "precedence": 1,
        # 0 = Left, 1 = Right, 2 = None
        "associativity": 0,
    },
    "-": {
        "precedence": 1,
        # 0 = Left, 1 = Right, 2 = None
        "associativity": 0,
    },
}

T = TypeVar("T")


class Cursor(ABC, Generic[T]):
    def __init__(self, input: list[T]) -> None:
        super().__init__()
        self.input = input
        self.at = 0

    def peek(self) -> T | None:
        if self.at == 0:
            return self.input[0]
        else:
            if 0 >= self.at + 1 > len(self.input):
                return None
            return self.input[self.at + 1]

    def advance(self) -> None:
        self.at += 1

    def current(self) -> T | None:
        if self.at >= len(self.input):
            return None
        return self.input[self.at]
