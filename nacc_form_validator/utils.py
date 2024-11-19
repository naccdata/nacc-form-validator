"""Utility functions."""

import logging
import re
from typing import Any

from dateutil import parser

log = logging.getLogger(__name__)


def convert_to_date(value) -> Any:
    """Convert the input value to date object.

    Args:
        value: value to convert

    Returns:
        Any: date object or original value if conversion failed
    """
    if not isinstance(value, str):
        raise ValueError(
            f'"convert to date" not supported for non string value {value}')

    yearfirst = False
    if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", value):
        yearfirst = True

    try:
        return parser.parse(value, yearfirst=yearfirst).date()
    except (ValueError, TypeError, parser.ParserError) as error:
        raise parser.ParserError(error) from error


def convert_to_datetime(value) -> Any:
    """Convert the input value to datetime object.

    Args:
        value: value to convert

    Returns:
        Any: datetime object or original value if conversion failed
    """

    if not isinstance(value, str):
        raise ValueError(
            f'"convert to datetime" not supported for non string value {value}'
        )

    yearfirst = False
    if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", value):
        yearfirst = True

    try:
        return parser.parse(value, yearfirst=yearfirst)
    except (ValueError, TypeError, parser.ParserError) as error:
        raise parser.ParserError(error) from error


def compare_values(comparator: str, value: object, base_value: object) -> bool:
    """Compare two values.

    Args:
        comparator: str, The comparator
        value: The value being evaluated on
        base_value: The value being evaluated against

    Returns:
        bool: True if the formula is satisfied, else False
    """
    # test these first as they don't care about null values
    if comparator == "==":
        return value == base_value

    if comparator == "!=":
        return value != base_value

    # for < and >, follow same convention as jsonlogic for null values
    # for >= and <=, allow equality case (both None)
    if value is None and base_value is None:
        return True if comparator in ["<=", ">="] else False
    if value is None:
        return True if comparator in ["<", "<="] else False
    if base_value is None:
        return False if comparator in ["<", "<="] else True

    # now try as normal
    if comparator == ">=":
        return value >= base_value

    if comparator == ">":
        return value > base_value

    if comparator == "<=":
        return value <= base_value

    if comparator == "<":
        return value < base_value

    raise TypeError(f"Unrecognized comparator: {comparator}")
