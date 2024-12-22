from abc import ABC
from ast import Expr
from typing import Generic, Callable, TypeVar

from common import TT, Cursor, PrimitiveTypes, bcolors, operators
from ast_exprs import (
    AstirExpr,
    ShuntingYardAlgorithmResults,
    Identifier,
    Literal,
    PrimitiveType,
    Reference,
    AstirTuple,
    SymbolTable,
    Parameter,
    Symbol,
    Parenthesized,
    Lambda,
    Assignment,
    Application,
    check_is_allowed,
)


class Token:
    def __init__(
        self, ty: TT | None, prim_ty: PrimitiveTypes | None = None, val=None
    ) -> None:
        if ty == None:
            raise Exception("Token type was none...")
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
            string = self.collect_until(lambda c, _: (c is None) or c == '"')
            return Token(TT.LITERAL, prim_ty=PrimitiveTypes.STR, val=string)
        elif c not in TT and (is_valid_ident(c) or c == "."):
            self.advance()
            if (next := self.current()) and next == "'" and c == "d":
                # self.advance()
                return Token(TT.PRIME_FORM)

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
        return Token(None)


class Parser(Cursor):
    def __init__(self, input: list[Token]) -> None:
        super().__init__(input)
        self.results: list["AstirExpr"] = []
        global_symbols = SymbolTable(0)
        # TODO: we are waiting for typedef!
        global_symbols.insert("int", PrimitiveType(PrimitiveTypes.INT))
        global_symbols.insert("unit", PrimitiveType(PrimitiveTypes.UNIT))
        global_symbols.insert("str", PrimitiveType(PrimitiveTypes.STR))
        global_symbols.insert("float", PrimitiveType(PrimitiveTypes.FLOAT))

        self.symbol_tables: dict[int, SymbolTable] = {0: global_symbols}
        self.using_st: int = 0
        self.parsing_lambda_parameters = False
        self.op_stack: list[str] = []
        # temp solution
        self.current_number_of_advances = 0
        self.already_parsing_sya = False

    def resolve_type(self, ty: Expr) -> None:
        pass

    def advance(self) -> None:
        self.current_number_of_advances += 1
        return super().advance()

    def peek(self, amt: int = 1) -> Token | None:
        if self.at + amt > len(self.input):
            return None
        return self.input[self.at + amt]

    def lookup(self, name: str, symbol_table_id: int | None = None) -> Symbol | None:
        symbol_table_id = self.using_st if symbol_table_id is None else symbol_table_id
        if symbol_table_id is None or symbol_table_id not in self.symbol_tables:
            return None
        symbol_table = self.symbol_tables[symbol_table_id]
        symbol = symbol_table.lookup(name)
        if symbol is None and (symbol_table.parent is not None):
            return self.lookup(name, symbol_table.parent)
        return symbol

    def parse_all(self) -> None:
        while c := self.current():
            if c == None:
                break
            parsed = self.parse()
            if parsed is None:
                break
            self.results.append(parsed)
            self.current_number_of_advances = 0
            self.using_st = 0

    def parse(self) -> AstirExpr | None:
        c = self.current()
        result: AstirExpr | None = None
        if c is None:
            return None

        # elif c.ty == TT.PRIME_FORM:
        #     self.advance()
        #     if (next := self.current()) and next.ty != TT.IDENT:
        #         raise Exception(
        #             f"Expected double colon after the prime form...got {next}"
        #         )
        #     ident = self.parse()
        #     self.advance()
        #     parts: list[Expr] = []
        #     while True:
        #         c = self.current()
        #         if c is None:
        #             break
        #         elif c.ty == TT.PIPE:
        #             self.advance()
        #             continue
        #         part = self.parse()
        #         if (
        #             not isinstance(part, Tuple)
        #             and not isinstance(part, Reference)
        #             and not isinstance(part, PrimitiveType)
        #             and (
        #                 not isinstance(part, Identifier)
        #                 or (isinstance(part, Identifier) and part.for_assignment)
        #             )
        #         ):
        #             self.at -= 1
        #             break

        #         parts.append(part)

        #     result = CustomDataType(ident, parts)
        elif c.ty == TT.LITERAL:
            if c.prim_ty is None or c.val is None:
                raise Exception("Invalid primitive type...how?")
            self.advance()
            result = Literal(c.prim_ty, c.val)
        elif c.ty == TT.IDENT:
            if c.val is None:
                raise Exception("Identifier with no value?")
            symbol = self.lookup(c.val)
            if symbol is not None:
                self.advance()
                result = Reference(c.val, symbol.belongs_to, symbol.id)
            else:
                next = self.input[self.at + 1]
                if (
                    next is not None
                    and next.ty is TT.IDENT
                    and self.parsing_lambda_parameters
                    and self.using_st in self.symbol_tables
                ):
                    self.advance()
                    sym_table = self.symbol_tables[self.using_st]
                    expr = self.parse()
                    if expr is not None and isinstance(expr, Reference):
                        sym_table.insert(c.val, expr)
                        result = Parameter()
                # elif next.ty is TT.OPEN_PAREN:
                #     self.advance()
                #     paren = self.parse()
                #     # raise Exception(f"Enum value(?): {c.val} -> {paren}")
                #     result = DataVariantWithInnerValue(Identifier(c.val), paren)
                else:
                    self.advance()
                    for_assignment = False
                    if (
                        (c2 := self.current())
                        and c2 is not None
                        and c2.ty == TT.BACKSLASH
                    ):
                        for_assignment = True
                    result = Identifier(c.val, for_assignment)

        elif c.ty == TT.OPEN_PAREN:
            self.advance()
            the_between: list[AstirExpr] = []
            has_comma: bool = False
            while True:
                c = self.current()
                if c is not None:
                    if c.ty == TT.CLOSE_PAREN:
                        self.advance()
                        break
                    elif c.ty == TT.COMMA:
                        self.advance()
                        has_comma = True
                        continue

                expr = self.parse()
                if expr is None:
                    self.at -= 1
                    break
                the_between.append(expr)
            if len(the_between) == 0:
                # We init Parenthesized with no expression so
                # that it is treated as an empty tuple, non value
                # or dead value. Its just a placeholder ig?
                result = Parenthesized(ty=PrimitiveTypes.UNIT)
            elif len(the_between) == 1:
                # Init Parenthesized with an expression (the_between[0])
                # to do exactly what it says... for example (\ :: int ...)
                result = Parenthesized(
                    PrimitiveType(PrimitiveTypes.UNIT), the_between[0]
                )
            elif len(the_between) > 1 and has_comma:
                # Handle tuples
                result = AstirTuple(the_between)

            # TODO: handle all function call arg parsing
            # function calls can use () but are not required
            # all this should be handled down where the
            # infix operators are but check if the previous
            # expression was a reference, or fn def and
            # then match arguments with arguments.
        elif c.ty == TT.BACKSLASH:
            self.advance()
            previous_symbol_table_id = self.using_st
            symbol_table_id = list(self.symbol_tables.items())[-1][0] + 1
            lambda_symbol_table = SymbolTable(symbol_table_id, 0)
            self.symbol_tables[symbol_table_id] = lambda_symbol_table
            self.using_st = symbol_table_id
            self.parsing_lambda_parameters = True
            while True:
                c = self.current()
                if c is not None:
                    if c.ty == TT.COMMA:
                        self.advance()
                        continue
                    elif c.ty == TT.DOUBLE_COLON:
                        self.advance()
                        ret_type = self.parse()
                        if ret_type is None:
                            raise Exception(
                                f"Return type was not there or non identifier ({ret_type})"
                            )
                        lambda_symbol_table.insert("ret", ret_type)
                        self.symbol_tables[symbol_table_id] = lambda_symbol_table
                        c = self.current()
                        if c is None or c.ty is not TT.FUNCTION_ARROW:
                            raise Exception(
                                f"Expected f.n. arrow after ret type... ({c})"
                            )
                        self.advance()
                        break
                expr = self.parse()
                if expr is None or not isinstance(expr, Parameter):
                    self.at -= 1
                    break
            body = self.parse()
            if body is None:
                raise Exception(f"Lambda must have body {self.current()}")
            popped = self.results.pop()
            if not isinstance(popped, Identifier):
                return popped
            symbol_table = self.symbol_tables[previous_symbol_table_id]
            _lambda = Lambda(lambda_symbol_table, body, previous_symbol_table_id, symbol_table.usable_id)
            symbol_table.insert(popped.value, _lambda)
            result = Assignment(
                popped,
                _lambda,
            )

        if result is None:
            raise Exception("Failed to parse ANYTHING.")
        # At this point, past previous parsing, we should have advanced past
        # the last token and now be face-to-face with the rare, elusive, OP!
        c = self.current()

        if (
            isinstance(result, Reference)
            and len(self.symbol_tables) > result.belongs_to >= 0
            # and c is not None
        ):
            st = self.symbol_tables[result.belongs_to]
            symbol = st.lookup_by_id(result.symbol_id)
            if symbol is None:
                raise Exception(f"Unkown symbol reference: {result}")
            if isinstance(symbol.val, Lambda):
                parameters = symbol.val.definition.parameters
                p_len = len(parameters.symbols.keys())

                # if its 1 then it HAS to be the return type...right?
                # we can pass on doing anything. Leave the reference
                # as is as no further handling is needed. However,
                # we will flip the "copy_val" on the reference so later
                # steps can quickly handle it
                if p_len == 1:
                    result.copy_val = True
                    return result
                elif p_len > 1:
                    # NOW we have more arguments so we will want to parse more.
                    self.current_number_of_advances = 0
                    possible_args: list[AstirExpr] = []

                    for k, ref in parameters.symbols.items():
                        if ref.name == "ret":
                            continue
                        elif not isinstance(ref.val, Reference):
                            break
                        type_symbol = self.lookup(ref.val.name, ref.val.belongs_to)
                        if type_symbol is None or not isinstance(
                            type_symbol.val, PrimitiveType
                        ):
                            break
                        possible_arg = self.parse()
                        if possible_arg is None:
                            raise Exception("Failed to parse")

                        if possible_arg.ty != type_symbol.val.ty:
                            raise Exception(
                                f"{bcolors.FAIL}{bcolors.BOLD}Type mismatch{bcolors.ENDC}"
                            )
                        elif (
                            possible_arg is None
                            or possible_arg.ty is None
                            # or not isinstance(possible_arg.ty, Symbol)
                        ):
                            raise Exception(
                                f"Null type? 1. {possible_arg is None} 2. {possible_arg.ty is None} 3. {not isinstance(possible_arg.ty, Symbol)} {bcolors.OKCYAN}{bcolors.BOLD}({possible_arg.ty}){bcolors.ENDC}"
                            )
                        possible_args.append(possible_arg)
                    if len(possible_args) == 0:
                        print("no possible args")
                        self.at = self.at - self.current_number_of_advances
                        self.current_number_of_advances = 0
                        return result

                    return Application(
                        Reference(symbol.name, symbol.belongs_to, symbol.id, False),
                        possible_args,
                    )
        possible_op = get_op(c)
        if not check_is_allowed(result) or result is None or self.already_parsing_sya:
            return result
        if possible_op is None:
            return result

        self.advance()
        # NOW WE START! begin working with the shunting yard algorithm
        # for parsing arithmetic
        self.op_stack.append(possible_op[0])
        self.already_parsing_sya = True
        res: list[AstirExpr | str] = [result]
        while True:
            c = self.current()
            possible_op = get_op(c)
            if c is None:
                break
            elif possible_op is not None:
                self.op_stack.append(possible_op[0])
                self.advance()
                continue

            parsed = self.parse()
            if not check_is_allowed(parsed) or parsed is None:
                self.at -= 1
                break
            res.append(parsed)
        res.extend(self.op_stack)
        self.op_stack = []
        sya_res = ShuntingYardAlgorithmResults(self.op_stack, res)
        self.already_parsing_sya = False
        return sya_res  # type: ignore
