from abc import ABC
from common import PrimitiveTypes, bcolors
from typing import Any, Union

class AstirExpr(ABC):
    def __init__(self, ty: Union['PrimitiveTypes', 'AstirExpr']):
        super().__init__()
        self.ty = ty
        

def check_is_allowed(AstirExpr: AstirExpr | None) -> bool:
    allowed = AstirExpr is not None or (
        isinstance(AstirExpr, Parenthesized)
        or isinstance(AstirExpr, Reference)
        or isinstance(AstirExpr, Literal)
    )
    if AstirExpr is not None and isinstance(AstirExpr, Identifier) and AstirExpr.for_assignment:
        allowed = False
    return allowed


class Symbol:
    def __init__(self, name: str, val: AstirExpr, belongs_to: int, id: int) -> None:
        super().__init__()
        self.name = name
        self.val = val
        self.belongs_to = belongs_to
        self.id = id

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

    def insert(self, name: str, val: AstirExpr) -> None:
        symbol = Symbol(name, val, self.id, self.usable_id)
        self.symbols[self.usable_id] = symbol
        self.name_to_id[name] = self.usable_id
        self.usable_id += 1

    def __repr__(self) -> str:
        return f"{self.symbols}"


class LambdaDefinition(AstirExpr):
    def __init__(
        self, parameters: SymbolTable# | list[PrimitiveTypes | AstirExpr]
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
        
        self.parameters=parameters

    def __repr__(self):
        return f"LambdaDef(Parameters={self.parameters})"


class Lambda(AstirExpr):
    def __init__(self, parameters: SymbolTable, body: AstirExpr, belongs_to: int, symbol_id: int):
        lambda_def = LambdaDefinition(parameters)
        super().__init__(lambda_def)
        self.definition = lambda_def
        self.belongs_to = belongs_to
        self.body = body
        self.symbol_id = symbol_id

    def __repr__(self):
        return f"Lambda(Def={self.definition}, Body={self.body})"

class Parenthesized(AstirExpr):
    def __init__(self, ty: AstirExpr | PrimitiveTypes, inner: AstirExpr | None = None) -> None:
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


class Parameter(AstirExpr):
    def __init__(self):
        super().__init__(PrimitiveTypes.UNIT)
    def __repr__(self) -> str:
        return f"Parameter"

class Assignment(AstirExpr):
    def __init__(self, left: AstirExpr, right: AstirExpr) -> None:
        super().__init__(PrimitiveTypes.UNIT)
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"Assignment ({self.left}) -> ({self.right})"


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


class Literal(AstirExpr):
    def __init__(self, literal_ty: PrimitiveTypes, val: Any) -> None:
        super().__init__(literal_ty)
        self.val = val

    def __repr__(self) -> str:
        return f"Literal(LTY={self.ty}, V={self.val})"


class PrimitiveType(AstirExpr):
    def __init__(self, inner: PrimitiveTypes) -> None:
        super().__init__(inner)
        self.val = inner

    def __repr__(self) -> str:
        return f"PrimitiveType(I={self.val})"


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
