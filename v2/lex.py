from typing import Callable
from shared import Cursor, PrimitiveTypes, TT, operators

class Token:
    def __init__(self, ty: TT, prim_ty: PrimitiveTypes | None = None, val=None) -> None:
        self.ty = ty
        self.val = val
        self.prim_ty = prim_ty

    def __repr__(self) -> str:
        return f"{self.ty} ({self.val})"


def get_op(possible_op: Token | None) -> tuple[str, dict[str, int]] | None:
    if (
        possible_op is None
        or possible_op.ty is None
        or possible_op.ty not in [TT.PLUS, TT.DASH]
    ):
        return None
    op = operators[possible_op.ty.value]
    return (possible_op.ty.value, op)


def is_valid_ident(c: str) -> bool:
    return c.isalnum() or c == "_"


class Lexer(Cursor):
    def __init__(self, input: str) -> None:
        super().__init__(list(input))
        self.results: list[Token] = []

    def lex_all(self) -> None:
        while c := self.current():
            if c == " " or c == "\n":
                self.advance()
                continue
            elif c == None:
                break
            lexed = self.lex()
            if lexed.ty == TT.COMMENT:
                self.advance()
                continue
            self.results.append(lexed)
            self.advance()

    def collect_until(
        self,
        check: Callable[[str | None, str], bool],
        devance_b4_break: bool = False,
        escape: bool = False,
        start_str: str = "",
    ) -> str:
        temp_str: str = start_str
        while True:
            c = self.current()
            if c is None or check(c, temp_str):
                if devance_b4_break:
                    self.at -= 1
                break
            self.advance()
            temp_str += c
        return temp_str

    def lex(self) -> Token:
        c = self.current()
        if c is None:
            raise Exception("Ran out of input")
        elif c == "/":
            if self.at + 1 < len(self.input) and self.input[self.at + 1] == "/":
                self.at += 2
                self.collect_until(lambda a, _: a == "\n", False)
                return Token(TT.COMMENT)
        elif c == ":" and self.input[self.at + 1] == ":":
            self.advance()
            return Token(TT.DOUBLE_COLON)
        elif c == '"':
            self.advance()
            string = ""
            while c := self.current():
                if c is None or c == '"':
                    break
                elif c == "\\":
                    self.advance()
                    c = self.current()
                    if c is None:
                        break
                    elif c == '"':
                        string += '"'
                        self.advance()
                        continue
                self.advance()
                string += c
            return Token(TT.LITERAL, prim_ty=PrimitiveTypes.STR, val=string)
        elif c not in TT and (is_valid_ident(c) or c == "."):
            self.advance()
            if (next := self.current()) and next == "'" and c in ["t", "d", "m"]:
                # self.advance()
                return Token(TT.PRIME_FORM, val=c)

            def identifier_check(c: str | None, rest: str) -> bool:
                if (c is None) or (not is_valid_ident(c)) and c != ".":
                    return True
                return False

            ident = self.collect_until(identifier_check, True, start_str=c)

            if "." in ident:
                try:
                    number = float(ident)
                    sign = 0 if number >= 0 else 1

                    number = abs(number)
                    integer = int(number)
                    fractional = number - integer
                    integer_bin = (
                        bin(integer).replace("0b", "") if integer != 0 else "0"
                    )

                    frac_bin: list[str] = (
                        []
                    )  # List to store the fractional binary digits
                    while (
                        fractional and len(frac_bin) < 23 + 3
                    ):  # Stop after 23+3 bits to avoid overflow
                        fractional *= 2  # Multiply by 2 to shift digits left
                        bit = int(fractional)  # Extract the integer part (0 or 1)
                        frac_bin.append(str(bit))  # Append the bit to the list
                        fractional -= (
                            bit  # Remove the integer part from the fractional value
                        )
                    frac_bin2: str = "".join(frac_bin)
                    combined_bin = integer_bin + "." + frac_bin2

                    if (
                        "1" in combined_bin
                    ):  # Ensure there is at least one significant bit
                        first_one = combined_bin.index(
                            "1"
                        )  # Find the position of the first '1'
                        if "." in combined_bin and first_one > combined_bin.index("."):
                            first_one -= (
                                1  # Adjust for the position of the binary point
                            )
                        exponent = (
                            len(integer_bin) - 1 - first_one
                        )  # Calculate the exponent from normalization
                        mantissa = (integer_bin + frac_bin2)[
                            first_one + 1 : first_one + 24
                        ]  # Extract mantissa bits
                    else:  # Special case for zero-like numbers
                        exponent = 0
                        mantissa = "0" * 23  # Mantissa is all zeros

                    # Step 4: Encode the exponent (add bias of 127)
                    exponent += 127  # Apply the bias to the exponent
                    exponent_bin = (
                        bin(exponent).replace("0b", "").zfill(8)
                    )  # Convert to 8-bit binary

                    # Step 5: Pad the mantissa to 23 bits
                    mantissa = mantissa.ljust(
                        23, "0"
                    )  # Ensure the mantissa has exactly 23 bits

                    # Combine the components into a 32-bit IEEE 754 representation
                    ieee754 = f"{sign}{exponent_bin}{mantissa}"
                    return Token(TT.LITERAL, val=ieee754, prim_ty=PrimitiveTypes.FLOAT)
                except ValueError:
                    raise Exception(
                        f'Something went wrong handling decimal: "{ident}"? check how many dots...'
                    )
            # TODO: TEMPORARY!!
            elif ident.isdigit():
                return Token(TT.LITERAL, val=int(ident), prim_ty=PrimitiveTypes.INT)
            return Token(TT.IDENT, val=ident)
        else:
            return Token(TT(c))
        return Token(TT.DUMMY)