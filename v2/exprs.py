from abc import ABC
from enum import Enum, auto
from typing import ForwardRef, Union

from shared import PrimitiveTypes


class TaggedType(ABC):
    pass


class AstirExpr(ABC):
    def __init__(self, ty: Union["TypeInstance", None]) -> None:
        if not isinstance(self, TaggedType) and ty is None:
            raise Exception(
                "Only expressions tagged as types may pass None to type parameter"
            )
        self.ty = ty

    def _type(self) -> Union["TypeInstance", None]:
        return self.ty


class Symbol:
    def __init__(
        self, name: str, inside: AstirExpr, belongs_to_table: int, id: int
    ) -> None:
        super().__init__()
        self.name = name
        self.inside = inside
        self.belongs_to_table = belongs_to_table
        self.id = id

    def __repr__(self) -> str:
        return f'Symbol "{self.name}", value = {self.inside}. Belongs to = {self.belongs_to_table}. ID = {self.id}'


class SymbolTable:
    def __init__(self, id: int, parent: int | None = None) -> None:
        self.symbols: dict[int, Symbol] = {}
        self.name_to_symbol: dict[str, int] = {}
        self.last_id = 0
        self.id = id
        self.parent = parent

    def lookup(self, to_find: str) -> Symbol | None:
        if (
            to_find not in self.name_to_symbol
            or self.name_to_symbol[to_find] not in self.symbols
        ):
            return None
        return self.symbols[self.name_to_symbol[to_find]]

    def insert(self, name: str, val: AstirExpr) -> Symbol:
        self.name_to_symbol[name] = self.last_id
        symbol = Symbol(name, val, self.id, self.last_id)
        self.symbols[self.last_id] = symbol
        self.last_id += 1
        return symbol

    def next_id(self) -> int:
        return self.last_id + 1

    def __repr__(self) -> str:
        return f"{self.symbols}"


class Identifier(AstirExpr, TaggedType):
    def __init__(self, value: str):
        super().__init__(None)
        self.value = value

    def __repr__(self):
        return f"Identifier(Value={self.value})"


class DataTypeDefinition(AstirExpr, TaggedType):
    def __init__(
        self,
        name: str,
        elements: AstirExpr | list[AstirExpr] | None,
        # E.g. d'List a :: ...
        # generic_params: [Identifier(value=a)]
        generic_params: list[Identifier],
    ):
        super().__init__(None)
        self.name: str = name
        self.elements: AstirExpr | list[AstirExpr] | None = elements
        self.generic_params = generic_params

    def __repr__(self):
        return f"DataTypeDefinition(Name={self.name}, Inside={self.elements}, Generics={self.generic_params})"


class Unit(AstirExpr):
    def __init__(self):
        super().__init__(PrimitiveTypes.UNIT)

    def __repr__(self):
        return "Unit"


class LambdaDefinition(AstirExpr, TaggedType):
    def __init__(
        self,
        name: str,
        parameter_types: list["TypeInstance"],
        generic_params: list[Identifier],
    ):
        super().__init__(None)
        self.name: str = name
        self.parameter_types: list["TypeInstance"] = parameter_types
        self.generic_params = generic_params


class Lambda(AstirExpr):
    def __init__(
        self, resolved_ty: AstirExpr, ty: "TypeInstance", parameters: SymbolTable
    ):
        super().__init__(ty)
        if self.ty is None or not isinstance(resolved_ty, LambdaDefinition):
            raise Exception("Expected LambdaDefinition type for Lambda.")
        self.name: str = resolved_ty.name
        self.parameters: SymbolTable = parameters


class TypeInstance(AstirExpr, TaggedType):
    def __init__(
        self,
        resolved_type: DataTypeDefinition | PrimitiveTypes,
        # E.g. \whatever List Int :: ...
        filled_in_generics: list["TypeInstance"] | None = [],
    ):
        super().__init__(self)
        self.resolved_type: DataTypeDefinition | PrimitiveTypes = resolved_type
        self.filled_in_generics: list["TypeInstance"] | None = filled_in_generics


class Dummy(AstirExpr):
    def __init__(self):
        super().__init__(PrimitiveTypes.UNIT)

class Parenthesized(AstirExpr, TaggedType):
    def __init__(self, values: list[AstirExpr]):
        super().__init__(None)
        self.values = values
# class Type:
#     def __init__(self, inside: PrimitiveTypes | AstirExpr):
#         if isinstance(inside, AstirExpr) and not isinstance(inside, TaggedType):
#             raise Exception(
#                 "Only expressions tagged as types are allowed to be passed into type class."
#             )
#         self.inside = inside


# if __name__ == "__main__":
#     symbol_table = SymbolTable()
#     ident = Lambda(
#         Type(LambdaDefinition("test_lambda", [Type(PrimitiveTypes.INT)])), symbol_table
#     )
#     print(ident._type())
