"""Datastore module."""

from abc import ABC, abstractmethod

# pylint: disable=(too-few-public-methods, no-self-use, unused-argument)


class Datastore(ABC):
    """Abstract class to represent the datastore (or warehouse) where previous
    records stored."""

    @abstractmethod
    def get_previous_instance(
            self, orderby: str, pk_field: str,
            current_ins: dict[str, str]) -> dict[str, str] | None:
        """Abstract method to return the previous instance of the specified
        record Override this method to retrieve the records from the desired
        datastore/warehouse.

        Args:
            orderby (str): Variable name that instances are sorted by
            pk_field (str): Primary key field of the project
            current_ins (dict[str, str]): Instance currently being validated

        Returns:
            dict[str, str]: Previous instance or None if no instance found
        """
        return None
