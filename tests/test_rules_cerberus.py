"""
Tests rules that are mainly handled by the Cerberus library (e.g. non-custom rules).
"""
def test_required(create_nacc_validator):
    """ Test required case """
    schema = {'dummy_var': {'required': True, 'type': 'string'}}
    nv = create_nacc_validator(schema)

    assert nv.validate({'dummy_var': 'hello'})
    assert not nv.validate({})
    assert nv.errors == {'dummy_var': ['required field']}

def test_nullable(create_nacc_validator):
    """ Test nullable case """
    schema = {'dummy_var': {'nullable': True, 'type': 'string'}}
    nv = create_nacc_validator(schema)

    assert nv.validate({'dummy_var': 'hello'})
    assert nv.validate({'dummy_var': ''})
    assert nv.validate({})

def test_minmax(create_nacc_validator):
    """ Test min/max case """
    schema = {
        "dummy_var": {
                "type": "integer",
                "required": True,
                "min": 0,
                "max": 10
            }
    }
    nv = create_nacc_validator(schema)

    for i in range(0, 10):
        assert nv.validate({'dummy_var': i})

    assert not nv.validate({'dummy_var': 11})
    assert nv.errors == {'dummy_var': ['max value is 10']}
    assert not nv.validate({'dummy_var': -1})
    assert nv.errors == {'dummy_var': ['min value is 0']}
    assert not nv.validate({'dummy_var': None})
    assert nv.errors == {'dummy_var': ['null value not allowed']}

def test_regex(create_nacc_validator):
    """ Test regex """
    schema = {
        "zip": {
            "type": "string",
            "nullable": True,
            "regex": "^(00[6-9]|0[1-9]\\d|[1-9]\\d{2})$"
        }
    }
    nv = create_nacc_validator(schema)

    assert nv.validate({'zip': "006"})
    assert nv.validate({'zip': "012"})
    assert nv.validate({'zip': "999"})

    assert not nv.validate({'zip': "6"})
    assert nv.errors == {'zip': ["value does not match regex '^(00[6-9]|0[1-9]\\d|[1-9]\\d{2})$'"]}
    assert not nv.validate({'zip': "12"})
    assert nv.errors == {'zip': ["value does not match regex '^(00[6-9]|0[1-9]\\d|[1-9]\\d{2})$'"]}
    assert not nv.validate({'zip': "1000"})
    assert nv.errors == {'zip': ["value does not match regex '^(00[6-9]|0[1-9]\\d|[1-9]\\d{2})$'"]}

def test_anyof(create_nacc_validator):
    """ Test anyof case """
    schema = {
        "dummy_var": {
            "type": "integer",
            "required": True,
            "anyof": [
                {
                    "min": 0,
                    "max": 10
                },
                {
                    "allowed": [99]
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    for i in range(0, 10):
        assert nv.validate({'dummy_var': i})
    assert nv.validate({'dummy_var': 99})
    assert not nv.validate({'dummy_var': 100})
    assert nv.errors == {'dummy_var': ['no definitions validate', {'anyof definition 0': ['max value is 10'], 'anyof definition 1': ['unallowed value 100']}]}
    assert not nv.validate({'dummy_var': -1})
    assert nv.errors == {'dummy_var': ['no definitions validate', {'anyof definition 0': ['min value is 0'], 'anyof definition 1': ['unallowed value -1']}]}

def test_date_format(date_constraint, create_nacc_validator):
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
