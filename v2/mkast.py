from shared import TT, PrimitiveTypes
from shared import Cursor
from exprs import (
    AstirExpr,
    DataTypeDefinition,
    Identifier,
    Parenthesized,
    SymbolTable,
    Symbol,
    Dummy,
    TypeInstance,
    Unit,
)
from lex import Token


class Lexer(Cursor):
    pass


class Parser(Cursor):
    def __init__(self, input: list[Token]):
        super().__init__(input)
        global_symbols: SymbolTable = SymbolTable(0)
        global_symbols.insert("Str", DataTypeDefinition("Str", None, []))

        self.all_symbol_tables: dict[int, SymbolTable] = {0: global_symbols}
        self.current_symbol_table: int = 0

    def lookup(self, name: str, symbol_table_id: int | None = None) -> Symbol | None:
        symbol_table_id = (
            self.current_symbol_table if symbol_table_id is None else symbol_table_id
        )
        if symbol_table_id not in self.all_symbol_tables:
            return None
        selected_symbol_table = self.all_symbol_tables[symbol_table_id]
        lookup = selected_symbol_table.lookup(name)
        if (
            lookup is None or name not in selected_symbol_table.name_to_symbol
        ) and selected_symbol_table.parent is not None:
            return self.lookup(name, selected_symbol_table.parent)
        else:
            return lookup

    def parse_all(self):
        while self.at < len(self.input):
            parsed = self.parse()
            if parsed is None:
                raise Exception("CANNOT PARSE NONE!")
            print(f"{parsed}")

    def parse(self) -> AstirExpr | None:
        current = self.current()
        result: AstirExpr | None = None
        if current is None:
            return None
        elif current.ty == TT.IDENT and current.val is not None:
            self.advance()
            ident_lookup = self.lookup(current.val)
            if ident_lookup is not None:
                print(ident_lookup)
            result = Identifier(current.val)
        elif current.ty == TT.OPEN_PAREN:
            self.advance()
            # if (current := self.current()) and current is not None:
            inside_of_parens: list[AstirExpr] = []
            while (
                (current := self.current())
                and current is not None
                and current.ty != TT.CLOSE_PAREN
            ):
                element = self.parse()
                if element is None:
                    raise Exception("Did not expect None value as element to () type")
                inside_of_parens.append(element)
            self.advance()
            if len(inside_of_parens) == 0:
                result = Unit()
            else:
                result = Parenthesized(inside_of_parens)
        elif current.ty == TT.PRIME_FORM and current.val is not None:
            self.advance()
            if current.val == "d":
                type_definition_name = self.parse()
                if not isinstance(type_definition_name, Identifier):
                    raise Exception(
                        "Expected an identifier as the name for a type defintion."
                    )
                possible_generics: list[Identifier] = []
                while (
                    (current := self.current())
                    and current is not None
                    and current.ty != TT.DOUBLE_COLON
                ):
                    parsed_generic = self.parse()
                    if not isinstance(parsed_generic, (Identifier)):
                        raise Exception(
                            "Unexpected expression in generic parameter list."
                        )
                    possible_generics.append(parsed_generic)
                self.advance()
                # if current.ty == TT.PIPE:
                #     self.advance()
                #     continue
                elements: list[AstirExpr] = []
                val_stack: list[AstirExpr] = []
                while (
                    (current := self.current())
                    and current is not None
                    and current.ty != TT.DOUBLE_COLON
                ):
                    if current.ty == TT.PIPE:
                        if len(val_stack) > 1:
                            elements.append(Parenthesized(val_stack))
                        else:
                            elements.append(val_stack[0])
                        val_stack = []
                        self.advance()
                        continue
                    value = self.parse()
                    if not isinstance(value, (Unit, Identifier, TypeInstance, Dummy, Parenthesized)):
                        raise Exception(
                            f"Unexpected value: {value} in data type definition"
                        )
                    val_stack.append(value)
                elements.append(Parenthesized(val_stack))
                val_stack=[]
                result = DataTypeDefinition(
                    type_definition_name.value, elements, possible_generics
                )

        return result
