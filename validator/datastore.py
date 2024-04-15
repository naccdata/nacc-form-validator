"""Datastore module."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from validator.nacc_validator import RecordType

# pylint: disable=(too-few-public-methods)


class Datastore(ABC):
    """Abstract class to represent the datastore (or warehouse) where previous
    records stored."""

    @abstractmethod
    def get_previous_instance(
            self, orderby: str, pk_field: str,
            current_ins: RecordType) -> RecordType:
        """Abstract method to return the previous instance of the specified
        record Override this method to retrieve the records from the desired
        datastore/warehouse.

        Args:
            orderby (str): Variable name that instances are sorted by
            pk_field (str): Primary key field of the project
            current_ins (dict[str, str]): Instance currently being validated

        Returns:
            dict[str, str]: Previous instance 
        """
        return {}
