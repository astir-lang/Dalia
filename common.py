from abc import ABC
from enum import Enum, auto
from typing import Generic, TypeVar


# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
# simple colors for now...just need help to see my eyes suck
class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class PrimitiveTypes(Enum):
    INT = auto()
    STR = auto()
    LIST = auto()
    FLOAT = auto()
    UNIT = auto()


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
    PIPE = "|"
    CLOSE_SQUARE = "]"
    IDENT = "IDENT"
    LITERAL = "LITERAL"
    COMMENT = "COMMENT"
    PRIME_FORM = "PRIME_FORM"
    DUMMY = "DUMMY"

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

    def advance(self) -> None:
        self.at += 1

    def current(self) -> T | None:
        if self.at >= len(self.input):
            return None
        return self.input[self.at]
