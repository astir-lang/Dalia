from abc import ABC
from common import TT, PrimitiveTypes, bcolors
from typing import Any, Union, Callable


class AstirExpr(ABC):
    def __init__(self, ty: Union["PrimitiveTypes", "AstirExpr"]):
        super().__init__()
        self.ty = ty


class Reference(AstirExpr):
    def __init__(
        self,
        name: str,
        belongs_to: int,
        symbol_id: int,
        copy_val: bool = False,
    ) -> None:
        super().__init__(PrimitiveTypes.UNIT)
        self.name = name
        self.symbol_id = symbol_id
        self.belongs_to = belongs_to
        self.copy_val = copy_val

    def __repr__(self) -> str:
        return f"Ref(ST={self.belongs_to}, Ref={self.name}, ID={self.symbol_id})"


class Symbol:
    def __init__(self, name: str, val: AstirExpr, belongs_to: int, id: int) -> None:
        super().__init__()
        self.name = name
        self.val = val
        self.belongs_to = belongs_to
        self.id = id

    def as_ref(self) -> Reference:
        return Reference(self.name, self.belongs_to, self.id, False)

    def __repr__(self) -> str:
        return (
            bcolors.WARNING
            + f'Symbol "{self.name}", value = {self.val}. Belongs to = {self.belongs_to}. ID = {self.id}'
            + bcolors.ENDC
        )


class SymbolTable:
    def __init__(self, id: int, parent: int | None = None) -> None:
        self.symbols: dict[int, Symbol] = {}
        self.name_to_id: dict[str, int] = {}
        self.usable_id = 0
        self.id = id
        self.parent = parent

    def lookup(self, name: str) -> Symbol | None:
        if name not in self.name_to_id:
            return None
        id = self.name_to_id[name]
        return self.lookup_by_id(id)

    def lookup_by_id(self, id: int) -> Symbol | None:
        if id not in self.symbols:
            return None
        return self.symbols[id]

    def insert(self, name: str, val: AstirExpr) -> Symbol:
        symbol = Symbol(name, val, self.id, self.usable_id)
        self.symbols[self.usable_id] = symbol
        self.name_to_id[name] = self.usable_id
        self.usable_id += 1

        return symbol

    def __repr__(self) -> str:
        return f"{self.symbols}"


class Parameter(AstirExpr):
    def __init__(self, name: str | None = None, val: AstirExpr | None = None, generic: bool = False):
        super().__init__(PrimitiveTypes.UNIT)
        self.name = name
        self.val = val,
        self.generic = generic

    def __repr__(self) -> str:
        return f"Parameter(Name={self.name}, Generic? {self.generic})"


class TypeClass(AstirExpr):
    def __init__(self, name: str, generics: list[AstirExpr], members: SymbolTable):
        super().__init__(self)
        self.members: SymbolTable = members
        self.name: str = name
        self.generics: list[AstirExpr] = generics


class Type(AstirExpr):
    def __init__(
        self,
        name: str,
        belongs_to: int,
        id: int,
        operators: list[TT] | None = None,
        generics: list[AstirExpr] = [],
        instances_of: list[Reference] = [],
    ):
        super().__init__(self)
        self.name = name
        self.operators = operators
        self.generics = generics
        self.belongs_to = belongs_to
        self.id = id


class TypeInstance(AstirExpr):
    def __init__(
        self,
        name: str,
        ty_belongs_to: int,
        type_id: int,
        filled_in_generics: list[AstirExpr] = [],
    ):
        super().__init__(self)
        self.name = name
        self.ty_belongs_to = ty_belongs_to
        self.type_id = type_id
        self.filled_in_generics = filled_in_generics

    def __repr__(self):
        return f"TypeInstance(NAME={self.name}, FILLED_IN_GENERICS={self.filled_in_generics})"


# Algebraic Data Type
class ADT(AstirExpr):
    def __init__(self, ty, name: str, values: list[AstirExpr]):
        super().__init__(ty)
        self.name = name
        self.values = values

    def __repr__(self):
        return (
            f"AlgebraicDataType(NAME={self.name}, TY={self.ty}, VALUES={self.values})"
        )


class Dummy(AstirExpr):
    def __init__(self):
        super().__init__(PrimitiveTypes.UNIT)


def check_is_allowed(AstirExpr: AstirExpr | None) -> bool:
    allowed = AstirExpr is not None or (
        isinstance(AstirExpr, Parenthesized)
        or isinstance(AstirExpr, Reference)
        or isinstance(AstirExpr, Literal)
    )
    if (
        AstirExpr is not None
        and isinstance(AstirExpr, Identifier)
        and AstirExpr.for_assignment
    ):
        allowed = False
    return allowed


class LambdaDefinition(AstirExpr):
    def __init__(
        self,
        parameters: SymbolTable,  # | list[PrimitiveTypes | AstirExpr]
        special_callable: Callable[[list[AstirExpr]], AstirExpr] | None = None,
    ):  # TODO: accept symboltable or list[AstirExpr]
        super().__init__(self)
        # todo:
        # lambda_parameter_types: list[PrimitiveTypes | AstirExpr] = []
        # if fix_params:
        #     if isinstance(parameters, SymbolTable):
        #         for i in parameters.symbols:
        #             symbol = parameters.symbols[i]
        #             if symbol is None:
        #                 raise Exception("How did a none value sneak in?")
        #             lambda_parameter_types.append(symbol.val.ty)
        #     else:
        #         lambda_parameter_types = parameters
        #     self.parameters = lambda_parameter_types

        self.parameters = parameters
        self.special_callable = special_callable

    def __repr__(self):
        return f"LambdaDef(Parameters={self.parameters})"


class InlineASM(AstirExpr):
    def __init__(self, lines: list[str]):
        super().__init__(PrimitiveTypes.UNIT)
        self.lines = lines

    def __repr__(self):
        return f"InlineASM(Lines={self.lines})"


class Lambda(AstirExpr):
    def __init__(
        self, parameters: SymbolTable, body: AstirExpr, belongs_to: int, symbol_id: int
    ):
        lambda_def = LambdaDefinition(parameters)
        super().__init__(lambda_def)
        self.definition = lambda_def
        self.belongs_to = belongs_to
        self.body = body
        self.symbol_id = symbol_id

    def __repr__(self):
        return f"Lambda(Def={self.definition}, Body={self.body})"


class Parenthesized(AstirExpr):
    def __init__(
        self, ty: AstirExpr | PrimitiveTypes, inner: AstirExpr | None = None
    ) -> None:
        super().__init__(ty)
        self.inner = inner

    def __repr__(self) -> str:
        return f"Parenthesized({self.inner})"


class ShuntingYardAlgorithmResults(AstirExpr):
    def __init__(self, operators: list[str], results: list[AstirExpr | str]) -> None:
        super().__init__(PrimitiveTypes.UNIT)
        self.oeprators = operators
        self.results = results

    def __repr__(self) -> str:
        return f"ShuntingYardAlgorithmResults({self.results}, ops={self.oeprators})"


class Identifier(AstirExpr):
    def __init__(self, value: str, for_assignment: bool = False) -> None:
        super().__init__(PrimitiveTypes.UNIT)
        self.value = value
        self.for_assignment = for_assignment

    def __repr__(self) -> str:
        return f"Ident({self.value})"


class AstirTuple(AstirExpr):
    def __init__(self, values: list[AstirExpr]) -> None:
        super().__init__(PrimitiveTypes.UNIT)
        self.values = values

    def __repr__(self) -> str:
        return f"Tuple({self.values})"


class Assignment(AstirExpr):
    def __init__(self, left: AstirExpr, right: AstirExpr) -> None:
        super().__init__(PrimitiveTypes.UNIT)
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"Assignment ({self.left}) -> ({self.right})"


class PrimitiveType(AstirExpr):
    def __init__(self, inner: PrimitiveTypes, size: int | None = None) -> None:
        super().__init__(inner)
        self.val = inner
        self.size = size

    def __repr__(self) -> str:
        return f"PrimitiveType(I={self.val}, SIZE={self.size})"


class Literal(AstirExpr):
    def __init__(self, literal_ty: PrimitiveType, val: Any) -> None:
        super().__init__(literal_ty)
        self.val = val

    def __repr__(self) -> str:
        return f"Literal(LTY={self.ty}, V={self.val})"


"""
d'Custom_data_type :: int
d'Custom_data_type :: str
d'Custom_data_type :: float
d'Custom_data_type :: ()
d'Custom_data_type :: OneVariant
d'Custom_data_type :: OneVariant | TwoVariant
d'Custom_data_type :: VariantWithData(int)
d'Option :: Some(int) | None
"""


class Application(AstirExpr):
    def __init__(self, lambda_ref: Reference, parameters: list[AstirExpr]):
        super().__init__(PrimitiveTypes.UNIT)
        self.lambda_ref = lambda_ref
        self.parameters = parameters

    def __repr__(self) -> str:
        return f"Application(Ref={self.lambda_ref}, P={self.parameters})"


# type: ignore
