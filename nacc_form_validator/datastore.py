"""Datastore module."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

# pylint: disable=(too-few-public-methods, no-self-use, unused-argument)


class Datastore(ABC):
    """Abstract class to represent the datastore (or warehouse) where previous
    records stored."""

    @abstractmethod
    def __init__(self, pk_field: str, orderby: str):
        """
        Args:
            pk_field: Primary key field to uniquely identify a participant
        """
        self.__pk_field = pk_field
        self.__orderby = orderby

    @property
    def pk_field(self) -> str:
        """primary key field.

        Returns:
            str: primary key field to uniquely identify a participant
        """
        return self.__pk_field

    @property
    def orderby(self) -> str:
        """order by field.

        Returns:
            str: field to sort the records by
        """
        return self.__orderby

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

    @abstractmethod
    def get_previous_nonempty_record(
            self, current_record: Dict[str, str], field: str) -> Optional[Dict[str, str]]:
        """Abstract method to return the previous record where field is NOT empty for the
        specified participant. Override this method to retrieve the records
        from the desired datastore/warehouse.

        Args:
            current_record: Record currently being validated
            field: Field to check for

        Returns:
            Dict[str, str]: Previous nonempty record or None if none found
        """
        return None
