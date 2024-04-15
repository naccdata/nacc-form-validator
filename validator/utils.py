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
    if re.match(r"(\d{4}-\d{2}-\d{2}|\d{4}\/\d{2}\/\d{2})", value):
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
    if re.match(r"(\d{4}-\d{2}-\d{2}|\d{4}\/\d{2}\/\d{2})", value):
        yearfirst = True

    try:
        return parser.parse(value, yearfirst=yearfirst)
    except (ValueError, TypeError, parser.ParserError) as error:
        raise parser.ParserError(error) from error
