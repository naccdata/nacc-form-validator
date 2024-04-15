from typing import Any, Dict, List, Mapping, Optional

from cerberus.errors import BasicErrorHandler, DocumentErrorTree


class Validator:
    schema: Optional[Mapping]
    error_handler: BasicErrorHandler
    document: Dict[str, Any]
    document_error_tree: DocumentErrorTree

    def _error(self, *args) -> None:
        ...

    def _validate_max(self, max_value: object, field: str, value: Any) -> None:
        ...

    def _validate_min(self, max_value: object, field: str, value: Any) -> None:
        ...

    def validate(self, document: Any, schema: Optional[Mapping]=None, update: bool=False, normalize:bool=True) -> bool:
        ...

    @property
    def errors(self) -> Dict[str, List[str]]:
        ...
