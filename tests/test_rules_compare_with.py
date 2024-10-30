"""
Tests the custom compare_with rule (_validate_compare_with).
"""
from utils import create_nacc_validator


def test_compare_with_current_year():
    """ Test compare_with operator, both with an adjustment and without; and with special key current_year """
    schema = {
        "birthyr": {
            "type": "integer",
            "required": True,
            "min": 1850,
            "compare_with": {
                "comparator": "<=",
                "base": "current_year"
            }
        },
        "birthyradj": {
            "type": "integer",
            "required": True,
            "min": 1850,
            "compare_with": {
                "comparator": "<=",
                "base": "current_year",
                "adjustment": 15,
                "op": "-"
            }
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'birthyr': 2000, 'birthyradj': 2000})

    # invalid cases - breaks min (so also testing min)
    assert not nv.validate({'birthyr': 1800, 'birthyradj': 1800})
    assert nv.errors == {'birthyr': ['min value is 1850'], 'birthyradj': ['min value is 1850']}

    # breaks current_year comparison - these will need to change once we hit 2038 :)
    assert not nv.validate({'birthyr': 2038, 'birthyradj': 2000})
    assert nv.errors == {'birthyr': ["input value doesn't satisfy the condition birthyr <= current_year"]}
    assert not nv.validate({'birthyr': 2023, 'birthyradj': 2023})
    assert nv.errors == {'birthyradj': ["input value doesn't satisfy the condition birthyradj <= current_year - 15"]}
    assert not nv.validate({'birthyr': 2038, 'birthyradj': 2038})
    assert nv.errors == {'birthyr': ["input value doesn't satisfy the condition birthyr <= current_year"], 'birthyradj': ["input value doesn't satisfy the condition birthyradj <= current_year - 15"]}

def test_compare_with_base_is_hardcoded():
    """ Test compare_with when the base is a hardcoded 0 """
    schema = {
        "test_var": {
            "type": "integer",
            "required": True,
            "compare_with": {
                "comparator": ">",
                "base": 0
            }
        }
    }
    nv = create_nacc_validator(schema)
    assert nv.validate({'test_var': 5})

    assert not nv.validate({'test_var': -1})
    assert nv.errors ==  {'test_var': ["input value doesn't satisfy the condition test_var > 0"]}
    assert not nv.validate({'test_var': 0})
    assert nv.errors ==  {'test_var': ["input value doesn't satisfy the condition test_var > 0"]}

def test_compare_with_adjustment_is_another_field():
    """ Test compare_with when the adjustment is another field """
    schema = {
        "base_value": {
            "type": "integer",
            "required": True,
        },
        "adjustment_value": {
            "type": "integer",
            "required": True,
        },
        "test_var": {
            "type": "integer",
            "required": True,
            "compare_with": {
                "comparator": "==",
                "base": "base_value",
                "adjustment": "adjustment_value",
                "op": "+"
            }
        }
    }
    nv = create_nacc_validator(schema)
    assert nv.validate({'test_var': 5, "base_value": 3, "adjustment_value": 2})
    assert nv.validate({'test_var': 5, "base_value": 4, "adjustment_value": 1})
    assert nv.validate({'test_var': 5, "base_value": 5, "adjustment_value": 0})
    assert nv.validate({'test_var': 5, "base_value": 8, "adjustment_value": -3})

    assert not nv.validate({'test_var': 5, "base_value": 5, "adjustment_value": 2})
    assert nv.errors == {'test_var': ["input value doesn't satisfy the condition test_var == base_value + adjustment_value"]}

def test_compare_with_absolute_value():
    """ Test compare_with absolute value operator """
    schema = {
        "waist1": {
            "type": "float",
            "required": True,
            "compare_with": {
                "comparator": "<=",
                "base": "waist2",
                "op": "abs",
                "adjustment": 0.5
            }
        },
        "waist2": {
            "type": "float",
            "required": True
        }
    }
    nv = create_nacc_validator(schema)
    assert nv.validate({'waist1': 5, 'waist2': 5})
    assert nv.validate({'waist1': 5, 'waist2': 5.5})
    assert nv.validate({'waist1': 5, 'waist2': 5.25})
    assert nv.validate({'waist1': 5, 'waist2': 4.5})
    assert nv.validate({'waist1': 5, 'waist2': 4.75})

    assert not nv.validate({'waist1': 5, 'waist2': 4.4})
    assert nv.errors ==  {'waist1': ["input value doesn't satisfy the condition abs(waist1 - waist2) <= 0.5"]}
    assert not nv.validate({'waist1': 5, 'waist2': 5.55})
    assert nv.errors ==  {'waist1': ["input value doesn't satisfy the condition abs(waist1 - waist2) <= 0.5"]}
