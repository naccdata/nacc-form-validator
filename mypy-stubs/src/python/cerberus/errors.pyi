from typing import Mapping, NamedTuple


class BasicErrorHandler:
    def _format_message(self, field: str, error: ValidationError) -> str:
        ...
    messages: Mapping[int,str]

class ErrorDefinition(NamedTuple):
    code: int
    rule: str

class ErrorTree:
    ...

class DocumentErrorTree(ErrorTree):
    ...

class ValidationError:
    ...
