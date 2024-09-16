"""
Tests the util methods in `utils.py`, which right now are just date conversion methods.
"""
import pytest

from dateutil import parser
from nacc_form_validator.utils import *


def test_convert_to_date():
    """ Test converting to a date """
    date = '01-01-2000'
    assert convert_to_date(date) == parser.parse(date).date()

def test_convert_to_date_yearfirst():
    """ Test converting to a date, year first """
    date = '2001-01-01'
    assert convert_to_date(date) == parser.parse(date, yearfirst=True).date()

def test_convert_to_date_notstr():
    """ Test converting invalid type to a date """
    date = 2000
    with pytest.raises(ValueError) as e:
        convert_to_date(date)
        raise ValueError(e)
    assert str(e.value) == '"convert to date" not supported for non string value 2000'

def test_convert_to_date_invalid():
    """ Test converting invalid date """
    date = "Thu INVALID 12 13:19:52 PDT 2024"
    with pytest.raises(parser.ParserError) as e:
        convert_to_datetime(date)
    assert str(e.value) == 'Unknown string format: Thu INVALID 12 13:19:52 PDT 2024'

def test_convert_to_datetime():
    """ Test converting to a datetime """
    date = '01-01-2000'
    assert convert_to_datetime(date) == parser.parse(date)

def test_convert_to_datetime_yearfirst():
    """ Test converting to a datetime, year first """
    date = '2001-01-01'
    assert convert_to_datetime(date) == parser.parse(date, yearfirst=True)

def test_convert_to_datetime_notstr():
    """ Test converting invalid type to a date """
    date = 5000
    with pytest.raises(ValueError) as e:
        convert_to_datetime(date)
        raise ValueError(e)
    assert str(e.value) == '"convert to datetime" not supported for non string value 5000'

def test_convert_to_datetime_invalid():
    """ Test converting invalid datetime """
    date = "Hello Sep 12 13:42:47 PDT 2024"
    with pytest.raises(parser.ParserError) as e:
        convert_to_datetime(date)
    assert str(e.value) == 'Unknown string format: Hello Sep 12 13:42:47 PDT 2024'
