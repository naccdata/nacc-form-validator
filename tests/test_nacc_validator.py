"""
Tests general NACCValidator (from nacc_validator.py) methods
"""
import pytest
from dateutil import parser
from nacc_form_validator.nacc_validator import ValidationException


def test_populate_data_types(nv):
    """ Checks dtypes are properly set (which is set with populate_data_types in the initializer) """
    assert nv.dtypes == {
        'dummy_int': 'int',
        'dummy_str': 'str',
        'dummy_float': 'float',
        'dummy_boolean': 'bool',
        'dummy_date': 'date',
        'dummy_datetime': 'datetime'
    }

def test_cast_record(nv):
    """ Test the cast_record method. """
    record = {
        'dummy_int': '10',
        'dummy_str': 'hello',
        'dummy_float': '1.2345',
        'dummy_boolean': '1',
        'dummy_date': '01-01-2000',
        'dummy_datetime': '2000-01-01'
    }

    assert nv.cast_record(record) == {
        'dummy_int': 10,
        'dummy_str': 'hello',
        'dummy_float': 1.2345,
        'dummy_boolean': True,
        'dummy_date': parser.parse('01-01-2000').date(),
        'dummy_datetime': parser.parse('2000-01-01', yearfirst=True)
    }

def test_cast_record_invalid(nv):
    """ Test the cast_record method; should not actually throw an error, but return the value as-is """
    record = {
        'dummy_int': 'hello',
        'dummy_float': 'world',
        'dummy_boolean': '',
        'dummy_date': 'invalid date',
        'dummy_datetime': 'invalid datetime'
    }

    assert nv.cast_record(record) == {
        'dummy_int': 'hello',
        'dummy_str': None,
        'dummy_float': 'world',
        'dummy_boolean': None,
        'dummy_date': 'invalid date',
        'dummy_datetime': 'invalid datetime'
    }

def test_validate_formatting_invalid_field(nv):
    """ Test _validate_formatting errors with invalid field - this is more
    of a test on getting system errors since its just a placeholder method """
    with pytest.raises(ValidationException):
        nv._validate_formatting(None, 'invalid_field', None)
    with pytest.raises(ValidationException):
        nv._validate_formatting(None, 'dummy_int', None)

    assert nv.sys_errors == {
        'invalid_field': ['formatting definition not supported for non string types'],
        'dummy_int': ['formatting definition not supported for non string types']
    }

def test_lots_of_rules(create_nacc_validator):
    """ Test when a specific field has a lot of rules associated with it (in this case oldadcid) """
    schema = {
        "adcid": {
            "type": "integer",
            "required": True,
            "min": 0,
            "max": 68
        },
        "prevenrl": {
            "type": "integer",
            "required": True,
            "allowed": [0, 1, 9]
        },
        "oldadcid": {
            "type": "integer",
            "nullable": True,
            "anyof": [
                {"min": 0, "max": 68},
                {"allowed": [-1]}
            ],
            "compatibility": [
                {
                    "index": 0,
                    "if": {
                        "prevenrl": {"allowed": [1]}
                    },
                    "then": {
                        "oldadcid": {"nullable": False}
                    }
                },
                {
                    "index": 1,
                    "if": {
                        "prevenrl": {"allowed": [0, 9]}
                    },
                    "then": {
                        "oldadcid": {"nullable": True, "filled": False}
                    }
                }
            ],
            "logic": {
                "formula": {
                    "!=": [
                        {"var": "oldadcid"},
                        {"var": "adcid"}
                    ]
                }
            }
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'adcid': 0, 'prevenrl': 1, 'oldadcid': -1})
    assert nv.validate({'adcid': 0, 'prevenrl': 1, 'oldadcid': 10})
    assert nv.validate({'adcid': 0, 'prevenrl': 0, 'oldadcid': None})
    assert nv.validate({'adcid': 0, 'prevenrl': 9, 'oldadcid': None})

    # invalid cases - compatibility
    assert not nv.validate({'adcid': 0, 'prevenrl': 1, 'oldadcid': None})
    assert nv.errors == {'oldadcid': ["('oldadcid', ['null value not allowed']) for {'prevenrl': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({'adcid': 0, 'prevenrl': 0, 'oldadcid': 1})
    assert nv.errors == {'oldadcid': ["('oldadcid', ['must be empty']) for {'prevenrl': {'allowed': [0, 9]}} - compatibility rule no: 1"]}

    # invalid cases, logic (adcid != oldadcid)
    assert not nv.validate({'adcid': 0, 'prevenrl': 1, 'oldadcid': 0})
    assert nv.errors == {'oldadcid': ['error in formula evaluation - value 0 does not satisfy the specified formula']}
