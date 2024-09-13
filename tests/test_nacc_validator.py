"""
Tests the NACCValidator (from nacc_validator.py)
"""
import pytest

from dateutil import parser
from nacc_form_validator.nacc_validator import (NACCValidator,
                                                CustomErrorHandler,
                                                ValidationException)

def create_nacc_validator(schema: dict[str, object]) -> NACCValidator:
    return NACCValidator(schema,
                         allow_unknown=False,
                         error_handler=CustomErrorHandler(schema))

@pytest.fixture
def nv():
    """ Returns a dummy QC with all data kinds of data types/rules to use for general testing """
    schema = {
        'dummy_int': {
            'nullable': True,
            'type': 'integer'
        },
        'dummy_str': {
            'nullable': True,
            'type': 'string'
        },
        'dummy_float': {
            'nullable': True,
            'type': 'float'
        },
        'dummy_boolean': {
            'nullable': True,
            'type': 'boolean'
        },
        'dummy_date': {
            'nullable': True,
            'type': 'date',
            'max': 3000
        },
        'dummy_datetime': {
            'nullable': True,
            'type': 'datetime'
        }
    }

    return create_nacc_validator(schema)

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

"""
The following test common rules used in NACC forms that are "custom" relative to what
the base Cerberus Validator provides.
"""

def test_required():
    schema = {'dummy_var': {'required': True, 'type': 'string'}}
    nv = create_nacc_validator(schema)

    assert nv.validate({'dummy_var': 'hello'})
    assert not nv.validate({})
    assert nv.errors == {'dummy_var': ['required field']}

def test_nullable():
    schema = {'dummy_var': {'nullable': True, 'type': 'string'}}
    nv = create_nacc_validator(schema)

    assert nv.validate({'dummy_var': 'hello'})
    assert nv.validate({'dummy_var': ''})
    assert nv.validate({})

@pytest.fixture
def date_constraint():
    return "(^(0[1-9]|1[0-2])[-\\/](0[1-9]|[12][0-9]|3[01])[-\\/](\\d{4})$)|(^(\\d{4})[-\\/](0[1-9]|1[0-2])[-\\/](0[1-9]|[12][0-9]|3[01])$)"

def test_date_format(date_constraint):
    """ Test dates schema from regex """
    schema = {
        "frmdate": {
            "required": True,
            "type": "string",
            "formatting": "date",
            "regex": date_constraint
        }
    }

    nv = create_nacc_validator(schema)
    assert nv.validate({'frmdate': '01/01/2001'})
    assert nv.validate({'frmdate': '2001/01/01'})

    assert not nv.validate({'frmdate': '01/01/01'})
    assert nv.errors == {'frmdate': [f"value does not match regex '{date_constraint}'"]}
    assert not nv.validate({'frmdate': 'hello world'})
    assert nv.errors == {'frmdate': [f"value does not match regex '{date_constraint}'"]}


def test_compatibility_if_then(nv):
    """ Tests if/then compatibility rule, which also tests '_validate_filled' by extension """
    schema = {
        "mode": {
            "required": True,
            "type": "integer",
            "allowed": [1, 2, 3]
        },
        "rmreason": {
            "nullable": True,
            "type": "integer",
            "compatibility": [
                {
                    "if": {
                        "mode": {
                            "allowed": [2]
                        }
                    },
                    "then": {
                        "nullable": False
                    }
                },
                {
                    "if": {
                        "mode": {
                            "allowed": [1, 3]
                        }
                    },
                    "then": {
                        "nullable": True,
                        "filled": False
                    }
                }
            ],
            "allowed": [1, 2, 3, 4, 5]
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    for i in range(1, 6):
        assert nv.validate({'mode': 2, 'rmreason': i})
    assert nv.validate({'mode': 1, 'rmreason': None})
    assert nv.validate({'mode': 3, 'rmreason': None})

    # invalid cases for first condition
    assert not nv.validate({'mode': 2, 'rmreason': 9})
    assert nv.errors == {'rmreason': ['unallowed value 9']}
    assert not nv.validate({'mode': 2, 'rmreason': None})
    assert nv.errors == {'rmreason': ["('rmreason', ['null value not allowed']) for {'mode': {'allowed': [2]}} - compatibility rule no: 1"]}

    # invalid cases for second condition
    assert not nv.validate({'mode': 3, 'rmreason': 1})
    assert nv.errors == {'rmreason': ["('rmreason', ['must be empty']) for {'mode': {'allowed': [1, 3]}} - compatibility rule no: 2"]}
    assert not nv.validate({'mode': 1, 'rmreason': 5})
    assert nv.errors == {'rmreason': ["('rmreason', ['must be empty']) for {'mode': {'allowed': [1, 3]}} - compatibility rule no: 2"]}
    assert not nv.validate({'mode': 1, 'rmreason': 9})
    assert nv.errors == {'rmreason': ['unallowed value 9', "('rmreason', ['must be empty']) for {'mode': {'allowed': [1, 3]}} - compatibility rule no: 2"]}

def test_logic_or():
    """ Test mathematical logic or case """
    schema = {
        "raceasian": {
            "type": "integer",
            "nullable": True,
            "allowed": [1]
        },
        "raceblack": {
            "type": "integer",
            "nullable": True,
            "allowed": [1]
        },
        "raceaian": {
            "type": "integer",
            "nullable": True,
            "allowed": [1],
            "logic": {
                "formula": {
                    "or": [
                        {"==": [1, {"var": "raceaian"}]},
                        {"==": [1, {"var": "raceasian"}]},
                        {"==": [1, {"var": "raceblack"}]},
                    ]
                }
            }
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'raceasian': 1})
    assert nv.validate({'raceblack': 1})
    assert nv.validate({'raceaian': 1, 'raceasian': None, 'raceblack': None})
    assert nv.validate({'raceaian': None, 'raceasian': 1, 'raceblack': 1})
    assert nv.validate({'raceaian': 1, 'raceasian': 1, 'raceblack': 1})
    assert not nv.validate({'raceaian': None, 'raceasian': None, 'raceblack': None})
    assert nv.errors == {'raceaian': ['error in formula evaluation - value None does not satisfy the specified formula']}
    assert not nv.validate({'raceaian': None})
    assert nv.errors == {'raceaian': ['error in formula evaluation - value None does not satisfy the specified formula']}

def test_compatibility_with_nested_logic():
    """ Test when the rule has a nested compatibility - logic """
    schema = {
        "raceasian": {
            "type": "integer",
            "nullable": True,
            "allowed": [1]
        },
        "raceblack": {
            "type": "integer",
            "nullable": True,
            "allowed": [1]
        },
        "raceaian": {
            "type": "integer",
            "nullable": True,
            "allowed": [1]
        },
        "raceunkn": {
            "type": "integer",
            "nullable": True,
            "allowed": [1],
            "compatibility": [
                {
                    "if": {
                        "logic": {
                            "formula": {
                                "or": [
                                    {"==": [1, {"var": "raceaian"}]},
                                    {"==": [1, {"var": "raceasian"}]},
                                    {"==": [1, {"var": "raceblack"}]}
                                ]
                            }
                        }
                    },
                    "then": {
                        "nullable": True,
                        "filled": False
                    }
                }
            ]
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({})  # since they're technically all optional
    assert nv.validate({'raceaian': 1})
    assert nv.validate({'raceasian': 1})
    assert nv.validate({'raceblack': 1})
    assert nv.validate({'raceunkn': 1})
    assert nv.validate({'raceunkn': 1, 'raceaian': None, 'raceasian': None, 'raceblack': None})
    assert nv.validate({'raceaian': 1, 'raceasian': 1, 'raceblack': 1})

    # the compatibility if/then with logic inside means that raceunkn cannot be 1 if any of the others are set
    assert not nv.validate({'raceaian': 1, 'raceunkn': 1})
    assert nv.errors == {'raceunkn': ["('raceunkn', ['must be empty']) for {'logic': {'formula': {'or': [{'==': [1, {'var': 'raceaian'}]}, {'==': [1, {'var': 'raceasian'}]}, {'==': [1, {'var': 'raceblack'}]}]}}} - compatibility rule no: 1"]}

# TODO: test temporal rules
