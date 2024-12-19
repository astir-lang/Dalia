from ast_exprs import Assignment, AstirExpr, Identifier, Lambda, Literal, Reference, ShuntingYardAlgorithmResults, Symbol, SymbolTable  # type: ignore
from common import Cursor, PrimitiveTypes


class ASM(Cursor):
    def __init__(
        self, input: list[AstirExpr], symbol_tables: dict[int, SymbolTable]
    ) -> None:
        super().__init__(input)
        self.lines: list[str] = [".global main", ".p2align 3"]
        self.symbol_tables: dict[int, SymbolTable] = symbol_tables
        # Format (ref_id, register)
        self.ref_id_and_register: list[tuple[int, int]] = []
        self.current_usable_register = 0

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
                to_add.append(f"{c_expr.left.value}:")
                print(f"Being added: {to_add}")
                generated_body = self.generate(c_expr.right.body)
                print(f"Generated body -> {generated_body}")
                to_add.extend(generated_body)
                to_add.append("ret")
                self.lines.extend(to_add)
        elif isinstance(c_expr, Reference):
            symbol = self.lookup_symbol(c_expr.belongs_to, c_expr.symbol_id)
            if symbol is None:
                raise Exception("failed to lookup symbol")
            if isinstance(symbol.val, Reference):
                symbol2 = self.lookup_symbol(
                    symbol.val.belongs_to, symbol.val.symbol_id
                )
                register = self.current_usable_register
                self.ref_id_and_register.append((symbol.val.symbol_id, register))
                to_add.append(f"x{register}")  # Temp
                self.current_usable_register += 1
        elif isinstance(c_expr, ShuntingYardAlgorithmResults):
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
                            register = self.current_usable_register
                            to_add.append(f"mov x{register}, {item1}")
                            item1 = f"x{register}"
                            self.current_usable_register += 1
                        print(
                            f"Adding last two items on stack: {item1}, {item2} = {item1 + item2}"
                        )
                        to_add.append(f"add x0, {item1}, {item2}")

            print(f"{c_expr}")
        return to_add
