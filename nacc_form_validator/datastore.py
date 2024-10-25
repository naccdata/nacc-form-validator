"""Datastore module."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

# pylint: disable=(too-few-public-methods, no-self-use, unused-argument)


class Datastore(ABC):
    """Abstract class to represent the datastore (or warehouse) where previous
    records stored."""

    @abstractmethod
    def __init__(self, pk_field: str):
        """
        Args:
            pk_field: Primary key field to uniquely identify a participant
        """
        self.__pk_field: str = pk_field
        super().__init__()

    @property
    def pk_field(self) -> str:
        """primary key field.

        Returns:
            str: primary key field to uniquely identify a participant
        """
        return self.__pk_field

    @abstractmethod
    def get_previous_record(
            self, current_record: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Abstract method to return the previous visit record for the
        specified participant. Override this method to retrieve the records
        from the desired datastore/warehouse.

        Args:
            current_record: Record currently being validated

        Returns:
            Dict[str, str]: Previous record or None if no previous record found
        """
        return None
