"""
Tests the custom compare_with_date rule (_validate_compare_with_date).
"""


def test_compare_age(date_constraint, create_nacc_validator):
    """ Tests compare_age, case where compare_to is another field"""
    schema = {
        "frmdate": {
            "type": "string",
            "formatting": "date",
            "regex": date_constraint,
            "compare_age": {
                "comparator": ">=",
                "birth_year": "birthyr",
                "birth_month": "birthmo",
                "compare_to": "behage"
            }

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
            "type": "integer"
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate(
        {'frmdate': '2024/02/02', 'birthmo': 6, 'birthyr': 1950, 'behage': 50})
    assert nv.validate(
        {'frmdate': '2024/02/02', 'birthmo': 2, 'birthyr': 2024, 'behage': 0})

    # invalid cases
    assert not nv.validate(
        {'frmdate': '2024/02/02', 'birthmo': 1, 'birthyr': 2024, 'behage': 50})
    assert nv.errors == {'frmdate': [
        "input value behage doesn't satisfy the condition: age at frmdate >= behage"
    ]}


def test_compare_age_list(date_constraint, create_nacc_validator):
    """ Tests compare_age, case where compare_to is a list """
    schema = {
        "frmdate": {
            "type": "string",
            "formatting": "date",
            "regex": date_constraint,
            "compare_age": {
                "comparator": ">=",
                "birth_year": "birthyr",
                "birth_month": "birthmo",
                "compare_to": [
                    "behage",
                    "cogage",
                    "perchage",
                    0
                ]
            }
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
            "type": "integer"
        },
        "cogage": {
            "type": "integer"
        },
        "perchage": {
            "type": "integer"
        },
        "motorage": {
            "type": "integer"
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'frmdate': '2024/02/02', 'birthmo': 6,
                       'birthyr': 1950, 'behage': 50, 'cogage': 40, 'perchage': 70})
    assert nv.validate({'frmdate': '2024/02/02', 'birthmo': 2,
                       'birthyr': 2024, 'behage': 0, 'cogage': 0, 'perchage': -2})

    # invalid cases
    assert not nv.validate({'frmdate': '2024/02/02', 'birthmo': 1,
                           'birthyr': 2024, 'behage': 50, 'cogage': 0, 'perchage': 60})
    assert nv.errors == {'frmdate': [
        "input value perchage doesn't satisfy the condition: age at frmdate >= behage, cogage, perchage, 0",
        "input value behage doesn't satisfy the condition: age at frmdate >= behage, cogage, perchage, 0"
    ]}


def test_compare_age_invalid_field(date_constraint, create_nacc_validator):
    """ Test case where invalid age to compare is provided """
    schema = {
        "frmdate": {
            "type": "string",
            "formatting": "date",
            "regex": date_constraint,
            "compare_age": {
                "comparator": "<=",
                "birth_year": "birthyr",
                "compare_to": "behage"
            }

        },
        "birthyr": {
            "type": "integer"
        },
        "behage": {
            "type": "string"
        }
    }

    nv = create_nacc_validator(schema)
    assert not nv.validate(
        {'frmdate': '2024/02/02', 'birthyr': 2024, 'behage': "dummy_str"})
    assert nv.errors == {'frmdate': [
        "Error in comparing behage to age at frmdate (0.08761122518822724): '<=' not supported between instances of 'float' and 'str'"]}


def test_compare_age_invalid_fields(create_nacc_validator):
    """ Test case where base_date or birth_year is invalid """
    schema = {
        "frmdate": {
            "type": "string",
            "compare_age": {
                "comparator": "<=",
                "birth_year": "birthyr",
                "compare_to": "behage",
            }

        },
        "birthyr": {
            "type": "integer"
        },
        "behage": {
            "type": "integer"
        }
    }

    nv = create_nacc_validator(schema)
    assert not nv.validate(
        {'frmdate': 'hello world', 'birthyr': 2024, 'behage': 50})
    assert nv.errors == {'frmdate': [
        'failed to convert value hello world to a date: Unknown string format: hello world']}
    assert not nv.validate(
        {'frmdate': '2024/02/02', 'birthyr': "", 'behage': 50})
    assert nv.errors == {
        'birthyr': ['must be of integer type'],
        'frmdate': ['Cannot compute birth date, one or more components empty'],
    }


def test_compare_age_null_base(create_nacc_validator):
    """ Test case where base_date is null """

    schema = {
        "frmdate": {
            "type": "string",
            "required": True,
            "compare_age": {
                "comparator": "<=",
                "birth_year": "birthyr",
                "compare_to": "behage",
            }
        },
        "birthyr": {
            "type": "integer"
        },
        "behage": {
            "type": "integer"
        }
    }

    nv = create_nacc_validator(schema)
    assert not nv.validate(
        nv.cast_record({'frmdate': '', 'birthyr': 2024, 'behage': 50}))
    assert nv.errors == {'frmdate': ['null value not allowed']}
