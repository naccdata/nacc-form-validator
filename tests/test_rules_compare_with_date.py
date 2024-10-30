"""
Tests the custom compare_with_date rule (_validate_compare_with_date).
"""
from utils import create_nacc_validator, date_constraint

def test_compare_with_date(date_constraint):
    """ Tests compare_with_date, simple case """
    schema = {
        "frmdate": {
            "type": "string",
            "formatting": "date",
            "regex": date_constraint,
            "compare_with_date": {
                "base_date": "01/01/2012",
                "comparator": ">="
            }
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'frmdate': "2024/02/02"})
    assert nv.validate({'frmdate': "01/01/2012"})

    # invalid cases
    assert not nv.validate({'frmdate': "2011/12/31"})
    assert nv.errors == {'frmdate': ["input value doesn't satisfy the date condition frmdate >= 2012-01-01"]}
    assert not nv.validate({'frmdate': "01/01/2011"})
    assert nv.errors == {'frmdate': ["input value doesn't satisfy the date condition frmdate >= 2012-01-01"]}

def test_compare_with_date_age(date_constraint):
    """ Tests compare_with_date, age case """
    schema = {
        "frmdate": {
            "type": "string",
            "formatting": "date",
            "regex": date_constraint
        },
        "birthmo": {
            "type": "integer",
            "min": 1,
            "max": 12
        },
        "birthyr": {
            "type": "integer"
        },
        "behage": {
            "type": "integer",
            "compare_with_date": {
                "base_date": "frmdate",
                "comparator": "<=",
                "use_age": {
                    "birth_year": "birthyr",
                    "birth_month": "birthmo"
                }
            }
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'frmdate': '2024/02/02', 'birthmo': 6, 'birthyr': 1950, 'behage': 50})
    assert nv.validate({'frmdate': '2024/02/02', 'birthmo': 2, 'birthyr': 2024, 'behage': 0})

    # invalid cases
    assert not nv.validate({'frmdate': '2024/02/02', 'birthmo': 1, 'birthyr': 2024, 'behage': 50})
    assert nv.errors == {'behage': ["input value doesn't satisfy the date condition behage <= age at frmdate"]}
