"""Datastore module."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

# pylint: disable=(too-few-public-methods, no-self-use, unused-argument)


class Datastore(ABC):
    """Abstract class to represent the datastore (or warehouse) where previous
    records stored."""

    @abstractmethod
    def __init__(self, pk_field: str, orderby: str):
        """
        Args:
            pk_field: primary key field to uniquely identify a participant
            orderby: field to sort the records by
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
            self, current_record: Dict[str, str],
            field: Tuple[str, List[str]]) -> Optional[Dict[str, str]]:
        """Abstract method to return the previous record where all fields are
        NOT empty for the specified participant. Override this method to
        retrieve the records from the desired datastore/warehouse.

        Args:
            current_record: Record currently being validated
            field: Field(s) to check for

        Returns:
            Dict[str, str]: Previous nonempty record or None if none found
        """
        return None

    @abstractmethod
    def is_valid_rxcui(self, drugid: int) -> bool:
        """Abstract method to check whether a given drug ID is valid RXCUI.
        Override this method to implement drug ID validation. Check
        https://www.nlm.nih.gov/research/umls/rxnorm/overview.html,
        https://mor.nlm.nih.gov/RxNav/

        Args:
            drugid: provided drug ID

        Returns:
            bool: True if provided drug ID is valid, else False
        """
        return False

    @abstractmethod
    def is_valid_adcid(self, adcid: int, own: bool) -> bool:
        """Abstract method to check whether a given ADCID is valid. Override
        this method to implement ADCID validation.

        Args:
            adcid: provided ADCID
            own: whether to check own ADCID or another center's ADCID

        Returns:
            bool: True if provided ADCID is valid, else False
        """
        return False
