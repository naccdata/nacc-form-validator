"""Tests the util methods in `utils.py`."""
import pytest
from dateutil import parser

from nacc_form_validator.utils import *


def test_convert_to_date():
    """Test converting to a date."""
    date = '01-01-2000'
    assert convert_to_date(date) == parser.parse(date).date()


def test_convert_to_date_yearfirst():
    """Test converting to a date, year first."""
    date = '2001-01-01'
    assert convert_to_date(date) == parser.parse(date, yearfirst=True).date()


def test_convert_to_date_notstr():
    """Test converting invalid type to a date."""
    date = 2000
    with pytest.raises(ValueError) as e:
        convert_to_date(date)
        raise ValueError(e)
    assert str(
        e.value) == '"convert to date" not supported for non string value 2000'


def test_convert_to_date_invalid():
    """Test converting invalid date."""
    date = "Thu INVALID 12 13:19:52 PDT 2024"
    with pytest.raises(parser.ParserError) as e:
        convert_to_datetime(date)
    assert str(
        e.value) == 'Unknown string format: Thu INVALID 12 13:19:52 PDT 2024'


def test_convert_to_datetime():
    """Test converting to a datetime."""
    date = '01-01-2000'
    assert convert_to_datetime(date) == parser.parse(date)


def test_convert_to_datetime_yearfirst():
    """Test converting to a datetime, year first."""
    date = '2001-01-01'
    assert convert_to_datetime(date) == parser.parse(date, yearfirst=True)


def test_convert_to_datetime_notstr():
    """Test converting invalid type to a date."""
    date = 5000
    with pytest.raises(ValueError) as e:
        convert_to_datetime(date)
        raise ValueError(e)
    assert str(
        e.value
    ) == '"convert to datetime" not supported for non string value 5000'


def test_convert_to_datetime_invalid():
    """Test converting invalid datetime."""
    date = "Hello Sep 12 13:42:47 PDT 2024"
    with pytest.raises(parser.ParserError) as e:
        convert_to_datetime(date)
    assert str(
        e.value) == 'Unknown string format: Hello Sep 12 13:42:47 PDT 2024'


def test_compare_values_numeric():
    """Test comparing two numeric values."""
    assert compare_values(">=", 2, 2)
    assert compare_values(">=", 2.5, 1)

    assert compare_values("<=", 2, 2.0)
    assert compare_values("<=", 1.5, 2.5)

    assert compare_values(">", 2, 1)
    assert compare_values("<", 1.99, 2.00)

    assert compare_values("==", 2.0, 2)
    assert compare_values("!=", 2.00, 1.99)


def test_compare_values_numeric_invalid():
    """Test comparing two numeric values fails the condition."""
    assert not compare_values(">=", 1, 3)
    assert not compare_values("<=", 3.5, 1.5)

    assert not compare_values(">", 1, 3)
    assert not compare_values("<", 3.5, 1.5)

    assert not compare_values("==", 1, 3)
    assert not compare_values("!=", 3.0, 3.000)


def test_compare_values_date():
    """Test comparing two dates."""
    assert compare_values(">=", parser.parse("01/01/2000"),
                          parser.parse("01/01/1999"))
    assert compare_values(">=", parser.parse("01/01/2000"),
                          parser.parse("01/01/2000"))
    assert compare_values(">=", parser.parse("12/01/2000"),
                          parser.parse("01/01/2000"))

    assert compare_values("<=", parser.parse("01/01/2000"),
                          parser.parse("01/01/2001"))
    assert compare_values("<=", parser.parse("01/01/2000"),
                          parser.parse("01/01/2000"))
    assert compare_values("<=", parser.parse("01/01/2000"),
                          parser.parse("12/01/2000"))

    assert compare_values(">", parser.parse("01/02/2000"),
                          parser.parse("01/01/2000"))
    assert compare_values("<", parser.parse("01/01/2000"),
                          parser.parse("01/02/2000"))

    assert compare_values("==", parser.parse("01/01/2000"),
                          parser.parse("01/01/2000"))
    assert compare_values("!=", parser.parse("01/01/2000"),
                          parser.parse("12/12/2012"))


def test_compare_values_date_invalid():
    """Test comparing two dates fails the condition."""
    assert not compare_values(">=", parser.parse("01/01/2000"),
                              parser.parse("01/01/2001"))
    assert not compare_values("<=", parser.parse("01/02/2000"),
                              parser.parse("01/01/1999"))

    assert not compare_values(">", parser.parse("01/01/2000"),
                              parser.parse("01/01/2001"))
    assert not compare_values("<", parser.parse("01/02/2000"),
                              parser.parse("01/01/1999"))

    assert not compare_values("==", parser.parse("01/01/2000"),
                              parser.parse("01/01/1999"))
    assert not compare_values("!=", parser.parse("01/01/2000"),
                              parser.parse("01/01/2000"))


def test_compare_values_type_error():
    """Test comparing two values of incompatible types or unrecognized
    comparator."""
    with pytest.raises(TypeError) as e:
        compare_values("*", 5, 10)
    assert str(e.value) == "Unrecognized comparator: *"

    with pytest.raises(TypeError) as e:
        compare_values("+", None, None)
    assert str(e.value) == "Unrecognized comparator: +"

    with pytest.raises(TypeError) as e:
        compare_values("<", 5, parser.parse("01/01/2000"))
    assert str(
        e.value
    ) == "'<' not supported between instances of 'int' and 'datetime.datetime'"

    with pytest.raises(TypeError) as e:
        compare_values("<", "01/01/2000", parser.parse("01/01/2000"))
    assert str(
        e.value
    ) == "'<' not supported between instances of 'str' and 'datetime.datetime'"


def test_compare_values_null_values_valid():
    """Test comparing when at least one of the values is null."""
    assert compare_values("==", None, None)
    assert not compare_values("==", None, 5)
    assert not compare_values("!=", None, None)
    assert compare_values("!=", 5, None)

    assert compare_values("<", None, 5)
    assert not compare_values("<", 5, None)
    assert not compare_values(">", None, 5)
    assert compare_values(">", 5, None)

    assert compare_values("<=", None, 5)
    assert not compare_values("<=", 5, None)
    assert not compare_values(">=", None, 5)
    assert compare_values(">=", 5, None)

    assert not compare_values("<", None, None)
    assert not compare_values(">", None, None)
    assert compare_values("<=", None, None)
    assert compare_values(">=", None, None)


def test_compare_values_precision_tolerance():
    """Test comparing values with precision tolerance."""
    assert compare_values("==", 1.33, 1.333333)
    assert not compare_values("==", 1.3, "1.333333")
    assert not compare_values("==", 1.33, 1.4)
    assert not compare_values("==", "1.33", "1.2")
    assert not compare_values("==", 1.33, 1.34)
    assert not compare_values("==", "3", 1.0)

    assert not compare_values("!=", 1.33, 1.333333)
    assert compare_values("!=", 1.3, "1.333333")
    assert compare_values("!=", 1.33, 1.4)
    assert compare_values("!=", "1.33", "1.2")
    assert compare_values("!=", 1.33, 1.34)
    assert compare_values("!=", "3", 1.0)

    assert compare_values("!=", "3", "hello")
    assert not compare_values("==", 2.5, "hello")
