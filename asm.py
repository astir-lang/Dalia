from abc import ABC
from ast_exprs import Application, Assignment, AstirExpr, Identifier, Lambda, LambdaDefinition, Literal, Reference, ShuntingYardAlgorithmResults, Symbol, SymbolTable  # type: ignore
from common import Cursor, PrimitiveTypes


class ASMFunction:
    def __init__(
        self, param_to_reg: dict[int, int], name_to_param: dict[str, int]
    ) -> None:
        self.param_to_reg = param_to_reg
        self.name_to_param = name_to_param
        # The next usable register is calculated by getting
        # the last inserted item in the self.param_to_reg
        # and by adding 1 to get us to the next x register
        self.next_usable_reg = (
            next(reversed(param_to_reg)) + 1 if len(param_to_reg) > 0 else 0
        )


class ASM(Cursor):
    def __init__(
        self, input: list[AstirExpr], symbol_tables: dict[int, SymbolTable]
    ) -> None:
        super().__init__(input)
        self.lines: list[str] = [".global _start", ".p2align 3"]
        self.symbol_tables: dict[int, SymbolTable] = symbol_tables
        # All tables related to registers most likely
        # have keys that map to a Symbol's id.
        # The inner dictionary holds the parameter index -> register
        # map. TODO: introduce a way to recognize different
        # register sizes for a64 (rn)
        self.fn_register_store: dict[int, ASMFunction] = {}
        self.inside_fn: int | None = None
        # # Format (ref_id, register)
        # self.ref_id_and_register: list[tuple[int, int]] = []
        # self.fn_register_man: dict[int, list[tuple[int, int]]] = {}
        # self.current_usable_register = 0

        # # This should be cleared after every generate call.
        # self.registers_in_use: list[Register] = []

    def is_register_reserved(self, register: int) -> bool:
        return False

    def current_fn(self) -> ASMFunction | None:
        if self.inside_fn is None:
            return None
        return self.fn_register_store[self.inside_fn]

    def generate_all(self):
        while self.current() is not None:
            generated = self.generate()
            self.lines.extend(generated)
            self.advance()

    def lookup_symbol(self, symbol_table: int, symbol_id: int) -> Symbol | None:
        if symbol_table not in self.symbol_tables:
            return None
        _symbol_table: SymbolTable | None = self.symbol_tables[symbol_table]
        if _symbol_table is None:
            return None
        symbol = _symbol_table.lookup_by_id(symbol_id)
        return symbol

    def generate(self, expr: AstirExpr | None = None) -> list[str]:
        c_expr = self.current() if expr is None else expr
        to_add: list[str] = []
        if isinstance(c_expr, Assignment):
            if isinstance(c_expr.right, Lambda) and isinstance(c_expr.left, Identifier):
                symbols = c_expr.right.definition.parameters.symbols
                last_used_register = 0
                lambda_param_to_register: dict[int, int] = {}
                param_name_to_idx: dict[str, int] = {}
                for symbol_idx in symbols:
                    symbol = symbols[symbol_idx]
                    if symbol.name == "ret":
                        # We break instead of continue because "ret"
                        # should always be the last item in the dict
                        break
                    lambda_param_to_register[symbol_idx] = last_used_register
                    param_name_to_idx[symbol.name] = symbol_idx
                    last_used_register += 1

                asm_function = ASMFunction(lambda_param_to_register, param_name_to_idx)
                self.fn_register_store[c_expr.right.symbol_id] = asm_function
                # This is so we can parse and get the correct arguments
                self.inside_fn = c_expr.right.symbol_id
                to_add.append(
                    f"{c_expr.left.value}: // Symbol ID: {c_expr.right.symbol_id}"
                )
                # to_add.append(f"// {asm_function.next_usable_reg}")
                to_add.extend(self.generate(c_expr.right.body))
                to_add.append("ret")
                self.inside_fn = None
        elif isinstance(c_expr, ShuntingYardAlgorithmResults):
            inside_fn = self.current_fn()
            if inside_fn is None:
                raise Exception("Out of place sya...")
            if len(c_expr.oeprators) > 0:
                raise Exception("Invalid shunting yard algorithm")
            stack: list[str] = []
            c_expr.results.reverse()
            while len(c_expr.results) > 0 and (term := c_expr.results.pop()):
                # TODO: make some like class method or something
                # to make this cleaner??
                if isinstance(term, Reference):
                    stack.extend(self.generate(term))
                elif isinstance(term, Literal):
                    if term.ty != PrimitiveTypes.INT:
                        raise Exception("Unexpected type.")
                    stack.append(str(term.val))
                elif isinstance(term, str):
                    if term == "+":
                        stack.reverse()
                        (item1, item2) = (stack.pop(), stack.pop())
                        if not item1.startswith("x"):
                            register = inside_fn.next_usable_reg
                            to_add.append(f"mov x{register}, {item1}")
                            item1 = f"x{register}"
                            inside_fn.next_usable_reg += 1
                        print(
                            f"Adding last two items on stack: {item1}, {item2} = {item1 + item2}"
                        )
                        to_add.append(f"add x0, {item1}, {item2}")
        elif isinstance(c_expr, Reference):
            symbol_in_ref: Symbol | None = self.lookup_symbol(
                c_expr.belongs_to, c_expr.symbol_id
            )
            if symbol_in_ref is None:
                raise Exception(f'Failed to lookup referenced symbol "{c_expr.name}"')
            if (
                (c_fn := self.current_fn())
                and c_fn is not None
                and c_expr.name in c_fn.name_to_param
                and c_fn.name_to_param[c_expr.name] in c_fn.param_to_reg
            ):
                register = c_fn.param_to_reg[c_fn.name_to_param[c_expr.name]]
                to_add.append(f"x{register}")
        elif isinstance(c_expr, Application):
            fn_parameters = self.fn_register_store[c_expr.lambda_ref.symbol_id]
            if fn_parameters is None:
                raise Exception("Failed to get reserved registers for fn")
            elif len(list(fn_parameters.param_to_reg.keys())) != len(c_expr.parameters):
                raise Exception("More parameters than reserved registers...")
            application_symbol: Symbol | None = self.lookup_symbol(
                c_expr.lambda_ref.belongs_to, c_expr.lambda_ref.symbol_id
            )
            if application_symbol is None:
                raise Exception(f"failed to find symbol {c_expr.lambda_ref.symbol_id}")
            elif (
                not isinstance(application_symbol.val, Lambda)
                or c_expr.lambda_ref.symbol_id not in self.fn_register_store
            ):
                raise Exception(
                    "Expected this symbol to come back to a lambda definition"
                )

            function_parameters = application_symbol.val.definition.parameters.symbols
            for idx, param in enumerate(c_expr.parameters):
                if not (0 <= idx < len(list(fn_parameters.param_to_reg.keys()))):
                    raise Exception(
                        "Invalid Application...More parameters than reserved registers"
                    )
                reserved_register = fn_parameters.param_to_reg[idx]
                if not isinstance(param, Literal) or param.ty != PrimitiveTypes.INT:
                    raise Exception("TODO: HANDLE MORE THAN JUST LITERALS")
                to_add.append(f"mov x{reserved_register}, {param.val}")
            to_add.append(f"bl {application_symbol.name}")

        return to_add
