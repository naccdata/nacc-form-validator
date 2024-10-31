"""
Tests the custom compatibility rule (_validate_compatibility).
"""
def test_compatibility_if_then(create_nacc_validator):
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
                        "mode": {"allowed": [2]}
                    },
                    "then": {
                        "rmreason": {"nullable": False}
                    }
                },
                {
                    "if": {
                        "mode": {"allowed": [1, 3]}
                    },
                    "then": {
                        "rmreason": {"nullable": True, "filled": False}
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
    assert nv.errors == {'rmreason': ["('rmreason', ['null value not allowed']) for {'mode': {'allowed': [2]}} - compatibility rule no: 0"]}

    # invalid cases for second condition
    assert not nv.validate({'mode': 3, 'rmreason': 1})
    assert nv.errors == {'rmreason': ["('rmreason', ['must be empty']) for {'mode': {'allowed': [1, 3]}} - compatibility rule no: 1"]}
    assert not nv.validate({'mode': 1, 'rmreason': 5})
    assert nv.errors == {'rmreason': ["('rmreason', ['must be empty']) for {'mode': {'allowed': [1, 3]}} - compatibility rule no: 1"]}
    assert not nv.validate({'mode': 1, 'rmreason': 9})
    assert nv.errors == {'rmreason': ['unallowed value 9', "('rmreason', ['must be empty']) for {'mode': {'allowed': [1, 3]}} - compatibility rule no: 1"]}

def test_compatibility_with_nested_logic_or(create_nacc_validator):
    """ Test when the rule has a nested compatibility - or logic """
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
                        "raceaian": {
                            "logic": {
                                "formula": {
                                    "or": [
                                        {"==": [1, {"var": "raceaian"}]},
                                        {"==": [1, {"var": "raceasian"}]},
                                        {"==": [1, {"var": "raceblack"}]}
                                    ]
                                }
                            }
                        }
                    },
                    "then": {
                        "raceunkn": {"nullable": True, "filled": False}
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
    assert nv.validate({'raceunkn': 1, 'raceaian': None, 'raceasian': None, 'raceblack': None})
    assert nv.validate({'raceaian': 1, 'raceasian': 1, 'raceblack': 1})

    # the compatibility if/then with logic inside means that raceunkn cannot be 1 if any of the others are set
    assert not nv.validate({'raceaian': 1, 'raceunkn': 1})
    assert nv.errors == {'raceunkn': ["('raceunkn', ['must be empty']) for {'raceaian': {'logic': {'formula': {'or': [{'==': [1, {'var': 'raceaian'}]}, {'==': [1, {'var': 'raceasian'}]}, {'==': [1, {'var': 'raceblack'}]}]}}}} - compatibility rule no: 0"]}
    assert not nv.validate({'raceasian': 1, 'raceunkn': 1})
    assert nv.errors == {'raceunkn': ["('raceunkn', ['must be empty']) for {'raceaian': {'logic': {'formula': {'or': [{'==': [1, {'var': 'raceaian'}]}, {'==': [1, {'var': 'raceasian'}]}, {'==': [1, {'var': 'raceblack'}]}]}}}} - compatibility rule no: 0"]}
    assert not nv.validate({'raceblack': 1, 'raceunkn': 1})
    assert nv.errors == {'raceunkn': ["('raceunkn', ['must be empty']) for {'raceaian': {'logic': {'formula': {'or': [{'==': [1, {'var': 'raceaian'}]}, {'==': [1, {'var': 'raceasian'}]}, {'==': [1, {'var': 'raceblack'}]}]}}}} - compatibility rule no: 0"]}

def test_multiple_compatibility(create_nacc_validator):
    """ Test multiple compatibility rules """
    schema = {
        "enrlgenoth": {
            "type": "integer",
            "nullable": True,
            "allowed": [1]
        },
        "enrlgenothx": {
            "type": "string",
            "nullable": True,
            "compatibility": [
                {
                    "index": 0,
                    "if": {
                        "enrlgenoth": {"allowed": [1]}
                    },
                    "then": {
                        "enrlgenothx": {"nullable": False}
                    }
                },
                {
                    "index": 1,
                    "if": {
                        "enrlgenoth": {"nullable": True, "filled": False}
                    },
                    "then": {
                        "enrlgenothx": {"nullable": True, "filled": False}
                    }
                }
            ]
        }
    }

    nv = create_nacc_validator(schema)

    # valid cases
    assert nv.validate({'enrlgenoth': 1, 'enrlgenothx': 'somevalue'})
    assert nv.validate({'enrlgenoth': None, 'enrlgenothx': None})
    assert nv.validate({})

    # invalid cases
    assert not nv.validate({'enrlgenoth': 1, 'enrlgenothx': None})
    assert nv.errors == {'enrlgenothx': ["('enrlgenothx', ['null value not allowed']) for {'enrlgenoth': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({'enrlgenoth': None, 'enrlgenothx': 'somevalue'})
    assert nv.errors == {'enrlgenothx': ["('enrlgenothx', ['must be empty']) for {'enrlgenoth': {'nullable': True, 'filled': False}} - compatibility rule no: 1"]}

def test_compatibility_multiple_variables_and(create_nacc_validator):
    """ Test when the compatibility relies on two variables on an "and" operator """
    schema = {
        "majordep": {
            "type": "integer",
            "required": True,
            "allowed": [0, 1, 2, 9]
        },
        "otherdep": {
            "type": "integer",
            "required": True,
            "allowed": [0, 1, 2, 9]
        },
        "deprtreat": {
            "type": "integer",
            "nullable": True,
            "allowed": [0, 1],
            "compatibility": [
                {
                    "if": {
                        "majordep": {"allowed": [0, 2, 9]},
                        "otherdep": {"allowed": [0, 2, 9]}
                    },
                    "then": {
                        "deprtreat": {"nullable": True, "filled": False}
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    # above schema is saying "If MAJORDEP and OTHERDEP in (0,2,9) then DEPRTREAT must be blank"
    assert nv.validate({"majordep": 0, "otherdep": 2, "deprtreat": None})
    assert nv.validate({"majordep": 1, "otherdep": 2, "deprtreat": 1})

    assert not nv.validate({"majordep": 0, "otherdep": 2, "deprtreat": 1})
    assert nv.errors == {'deprtreat': ["('deprtreat', ['must be empty']) for {'majordep': {'allowed': [0, 2, 9]}, 'otherdep': {'allowed': [0, 2, 9]}} - compatibility rule no: 0"]}
    assert not nv.validate({"majordep": 2, "otherdep": 9, "deprtreat": 0})
    assert nv.errors == {'deprtreat': ["('deprtreat', ['must be empty']) for {'majordep': {'allowed': [0, 2, 9]}, 'otherdep': {'allowed': [0, 2, 9]}} - compatibility rule no: 0"]}

def test_compatibility_multiple_variables_or(create_nacc_validator):
    """ Test when the compatibility relies on two variables on an "or" operator """
    schema = {
        "majordep": {
            "type": "integer",
            "required": True,
            "allowed": [0, 1, 2, 9]
        },
        "otherdep": {
            "type": "integer",
            "required": True,
            "allowed": [0, 1, 2, 9]
        },
        "deprtreat": {
            "type": "integer",
            "nullable": True,
            "allowed": [0, 1],
            "compatibility": [
                {
                    "if_op": "OR",
                    "if": {
                        "majordep": {"allowed": [1]},
                        "otherdep": {"allowed": [1]}
                    },
                    "then": {
                        "deprtreat": {"nullable": False}
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    # above schema is saying "If MAJORDEP or OTHERDEP is 1 then DEPRTREAT must be present"
    assert nv.validate({"majordep": 0, "otherdep": 2, "deprtreat": None})
    assert nv.validate({"majordep": 1, "otherdep": 2, "deprtreat": 1})
    assert nv.validate({"majordep": 9, "otherdep": 1, "deprtreat": 0})

    assert not nv.validate({"majordep": 1, "otherdep": 2, "deprtreat": None})
    assert nv.errors == {'deprtreat': ["('deprtreat', ['null value not allowed']) for {'majordep': {'allowed': [1]}, 'otherdep': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"majordep": 9, "otherdep": 1, "deprtreat": None})
    assert nv.errors == {'deprtreat': ["('deprtreat', ['null value not allowed']) for {'majordep': {'allowed': [1]}, 'otherdep': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"majordep": 1, "otherdep": 1, "deprtreat": None})
    assert nv.errors == {'deprtreat': ["('deprtreat', ['null value not allowed']) for {'majordep': {'allowed': [1]}, 'otherdep': {'allowed': [1]}} - compatibility rule no: 0"]}

def test_compatibility_then_multiple_blank_and(create_nacc_validator):
    """ Test when the rule results in multiple things needing to be blank """
    schema = {
        "parentvar": {
            "type": "integer",
            "nullable": True
        },
        "var3": {
            "type": "integer",
            "nullable": True
        },
        "var2": {
            "type": "integer",
            "nullable": True
        },
        "var1": {
            "type": "integer",
            "nullable": True,
            "compatibility": [
                {
                    "if": {
                        "parentvar": {"nullable": True,"filled": False}
                    },
                    "then": {
                        "var1": {"nullable": True,"filled": False},
                        "var2": {"nullable": True,"filled": False},
                        "var3": {"nullable": True,"filled": False}
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    # if parentvar is None then the following must be None: var1, var2, var3
    assert nv.validate({"parentvar": None, "var1": None, "var2": None, "var3": None})
    assert nv.validate({"parentvar": 0, "var1": 1, "var2": 2, "var3": 3})
    assert nv.validate({"parentvar": 0, "var1": None, "var2": 2, "var3": None})

    assert not nv.validate({"parentvar": None, "var1": 1, "var2": None, "var3": None})
    assert nv.errors == {'var1': ["('var1', ['must be empty']) for {'parentvar': {'nullable': True, 'filled': False}} - compatibility rule no: 0"]}
    assert not nv.validate({"parentvar": None, "var1": 1, "var2": 1, "var3": 1})
    assert nv.errors == {'var1': ["('var1', ['must be empty']) for {'parentvar': {'nullable': True, 'filled': False}} - compatibility rule no: 0"]}
    
    assert not nv.validate({"parentvar": None, "var1": None, "var2": None, "var3": 1})
    assert nv.errors == {'var1': ["('var3', ['must be empty']) for {'parentvar': {'nullable': True, 'filled': False}} - compatibility rule no: 0"]}

def test_compatibility_then_multiple_blank_logic_and(create_nacc_validator):
    """ Test when the rule results in multiple things needing to be blank - logic """
    schema = {
        "parentvar": {
            "type": "integer",
            "nullable": True
        },
        "var3": {
            "type": "integer",
            "nullable": True
        },
        "var2": {
            "type": "integer",
            "nullable": True
        },
        "var1": {
            "type": "integer",
            "nullable": True,
            "compatibility": [
                {
                    "if": {
                        "parentvar": {"nullable": True,"filled": False}
                    },
                    "then": {
                        "var1": {
                            "nullable": True,  # this is specifically required in schema for the None case
                            "logic": {
                                "formula": {
                                    "and": [
                                        {"==": [None, {"var": "var1"}]},
                                        {"==": [None, {"var": "var2"}]},
                                        {"==": [None, {"var": "var3"}]}
                                    ]
                                }
                            }
                        }
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    # if parentvar is None then the following must be None: var1, var2, var3
    assert nv.validate({"parentvar": None, "var1": None, "var2": None, "var3": None})
    assert nv.validate({"parentvar": 0, "var1": 1, "var2": 2, "var3": 3})
    assert nv.validate({"parentvar": 0, "var1": None, "var2": 2, "var3": None})

    assert not nv.validate({"parentvar": None, "var1": 1, "var2": None, "var3": None})
    assert nv.errors == {'var1': ["('var1', ['error in formula evaluation - value 1 does not satisfy the specified formula']) for {'parentvar': {'nullable': True, 'filled': False}} - compatibility rule no: 0"]}
    assert not nv.validate({"parentvar": None, "var1": 1, "var2": 1, "var3": 1})
    assert nv.errors == {'var1': ["('var1', ['error in formula evaluation - value 1 does not satisfy the specified formula']) for {'parentvar': {'nullable': True, 'filled': False}} - compatibility rule no: 0"]}
    
    # TODO: it looks like this error message is misleading, it fails because of var3 not var1 but since this logic is on var1 its reported as a var1 failure
    #       something to improve on. But also because of this you should avoid using logic and instead do it as shown in test_compatibility_then_multiple_blank_and
    assert not nv.validate({"parentvar": None, "var1": None, "var2": None, "var3": 1})
    assert nv.errors == {'var1': ["('var1', ['error in formula evaluation - value None does not satisfy the specified formula']) for {'parentvar': {'nullable': True, 'filled': False}} - compatibility rule no: 0"]}

def test_compatibility_multiple_resulting_variables_or(create_nacc_validator):
    """ Tests a "If X is 1, than Y or Z should be 1", and "If X i 0, then Y and Z should be 0" situation """
    schema = {
        "bevhall": {
            "type": "integer",
            "nullable": True
        },
        "beahall": {
            "type": "integer",
            "nullable": True
        },
        "hall": {
            "type": "integer",
            "required": True,
            "compatibility": [
                {
                    "then_op": "or",
                    "if": {
                        "hall": {"allowed": [1]}
                    },
                    "then": {
                        "bevhall": {"allowed": [1]},
                        "beahall": {"allowed": [1]}
                    }
                },
                {
                    "then_op": "and",
                    "if": {
                        "hall": {"allowed": [0]}
                    },
                    "then": {
                        "bevhall": {"allowed": [0]},
                        "beahall": {"allowed": [0]}
                    }
                }                
            ]
        }
    }
    nv = create_nacc_validator(schema)

    assert nv.validate({"hall": 1, "bevhall": 1, "beahall": 0})
    assert nv.validate({"hall": 1, "bevhall": 0, "beahall": 1})
    assert nv.validate({"hall": 1, "bevhall": 1, "beahall": 1})
    assert nv.validate({"hall": 5, "bevhall": 3, "beahall": 3})
    assert nv.validate({"hall": 1, "bevhall": 1, "beahall": None})
    assert nv.validate({"hall": 0, "bevhall": 0, "beahall": 0})

    assert not nv.validate({"hall": 1, "bevhall": 0, "beahall": 0})
    assert nv.errors == {'hall': ["('beahall', ['unallowed value 0']) for {'hall': {'allowed': [1]}} - compatibility rule no: 0", "('bevhall', ['unallowed value 0']) for {'hall': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"hall": 0, "bevhall": 0, "beahall": 1})
    assert nv.errors == {'hall': ["('beahall', ['unallowed value 1']) for {'hall': {'allowed': [0]}} - compatibility rule no: 1"]}
    assert not nv.validate({"hall": 0, "bevhall": None, "beahall": None})
    assert nv.errors == {'hall': ["('bevhall', ['null value not allowed']) for {'hall': {'allowed': [0]}} - compatibility rule no: 1"]}

def test_compatibility_multiple_resulting_options_or(create_nacc_validator):
    """ Tests a "If X is 1, than Y and Z should be 0 or 2" situation """
    schema = {
        "majdepdx": {
            "type": "integer",
            "nullable": True
        },
        "othdepdx": {
            "type": "integer",
            "nullable": True
        },
        "depd": {
            "type": "integer",
            "required": True,
            "compatibility": [
                {
                    "index": 0,
                    "if": {
                        "depd": {"allowed": [1]}
                    },
                    "then": {
                        "majdepdx": {"allowed": [0, 2]},
                        "othdepdx": {"allowed": [0, 2]}
                    }
                },
                {
                    "index": 2,
                    "if": {
                        "depd": {"allowed": [2]}
                    },
                    "then": {
                        "majdepdx": {"allowed": [1]},
                        "othdepdx": {"allowed": [1]}
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    assert nv.validate({"depd": 1, "majdepdx": 0, "othdepdx": 2})
    assert nv.validate({"depd": 1, "majdepdx": 2, "othdepdx": 2})
    assert nv.validate({"depd": 1, "majdepdx": 0, "othdepdx": 0})

    assert nv.validate({"depd": 0, "majdepdx": 0, "othdepdx": None})
    assert nv.validate({"depd": 0, "majdepdx": None, "othdepdx": 2})
    assert nv.validate({"depd": 5, "majdepdx": 1, "othdepdx": 1})

    assert not nv.validate({"depd": 2, "majdepdx": 0, "othdepdx": 2})
    assert nv.errors == {'depd': ["('majdepdx', ['unallowed value 0']) for {'depd': {'allowed': [2]}} - compatibility rule no: 2"]}
    assert not nv.validate({"depd": None, "majdepdx": 0, "othdepdx": 2})
    assert nv.errors == {'depd': ['null value not allowed']}

def test_compatibility_multiple_else(create_nacc_validator):
    """ Tests the else clause. If VAR1 is 1 then VAR2 is 2, else VAR2 3-5 """
    schema = {
        "var2": {
            "type": "integer",
            "required": True
        },
        "var1": {
            "type": "integer",
            "required": True,
            "compatibility": [
                {
                    "index": 0,
                    "if": {
                        "var1": {"allowed": [1]}
                    },
                    "then": {
                        "var2": {"allowed": [2]}
                    },
                    "else": {
                        "var2": {"allowed": [3, 4, 5]}
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    for i in range (3, 6):
        assert nv.validate({"var1": 0, "var2": i})
    assert nv.validate({"var1": 1, "var2": 2})

    assert not nv.validate({"var1": 0, "var2": 8})
    assert nv.errors == {'var1': ["('var2', ['unallowed value 8']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"var1": 1, "var2": 3})
    assert nv.errors == {'var1': ["('var2', ['unallowed value 3']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}

def test_compatibility_multiple_else_and_multiple_conditions(create_nacc_validator):
    """ Tests the else clause with multiple conditions. If VAR1 is 1 then VAR2 is 2, else VAR2 3-5 OR VAR3 is 9 """
    schema = {
        "var2": {
            "type": "integer",
            "nullable": True
        },
        "var3": {
            "type": "integer",
            "nullable": True
        },
        "var1": {
            "type": "integer",
            "required": True,
            "compatibility": [
                {
                    "index": 0,
                    "else_op": "or",
                    "if": {
                        "var1": {"allowed": [1]}
                    },
                    "then": {
                        "var2": {"allowed": [2]}
                    },
                    "else": {
                        "var2": {"allowed": [3, 4, 5]},
                        "var3": {"allowed": [9]}
                    }
                }
            ]
        }
    }
    nv = create_nacc_validator(schema)

    for i in range (3, 6):
        assert nv.validate({"var1": 0, "var2": i, "var3": None})
    assert nv.validate({"var1": 0, "var2": None, "var3": 9})
    assert nv.validate({"var1": 1, "var2": 2, "var3": None})

    assert not nv.validate({"var1": 1, "var2": 3, "var3": None})
    assert nv.errors == {'var1': ["('var2', ['unallowed value 3']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"var1": 1, "var2": None, "var3": 6})
    assert nv.errors == {'var1': ["('var2', ['null value not allowed']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}

    assert not nv.validate({"var1": 0, "var2": 8, "var3": None})
    assert nv.errors == {'var1': ["('var3', ['null value not allowed']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0", "('var2', ['unallowed value 8']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"var1": 0, "var2": None, "var3": None})
    assert nv.errors == {'var1': ["('var3', ['null value not allowed']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0", "('var2', ['null value not allowed']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}
    assert not nv.validate({"var1": 0, "var2": None, "var3": 16})
    assert nv.errors == {'var1': ["('var3', ['unallowed value 16']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0", "('var2', ['null value not allowed']) for {'var1': {'allowed': [1]}} - compatibility rule no: 0"]}

def test_compatibility_nested_anyof(create_nacc_validator):
    """ Tests when anyof is nested inside compatibility. """
    schema = {
        "menarche": {
            "nullable": True,
            "type": "integer",
            "anyof": [
                {"min": 5, "max": 25},
                {"allowed": [88,99]}
            ]
        },
        "nomensage": {
            "nullable": True,
            "type": "integer",
            "compatibility": [
                {
                    "index": 0,
                    "if": {
                        "menarche": {
                            "anyof": [
                                {"min": 5, "max": 25},
                                {"allowed": [99]}
                            ]
                        }
                    },
                    "then": {
                        "nomensage": {"nullable": False}
                    }
                },
                {
                    "index": 1,
                    "if": {
                        "menarche": {
                            "nullable": True,
                            "anyof": [
                                {"nullable": True, "filled": False},
                                {"allowed": [88]}
                            ]
                        }
                    },
                    "then": {
                        "nomensage": {"nullable": True, "filled": False}
                    }
                }
            ],
            "anyof": [
                {"min": 10,"max": 70},
                {"allowed": [88,99]}
            ]
        }
    }
    nv = create_nacc_validator(schema)

    for i in range (5, 26):
        assert nv.validate({"menarche": i, "nomensage": 20})
    assert nv.validate({"menarche": 99, "nomensage": 99})
    assert nv.validate({"menarche": None, "nomensage": None})
    assert nv.validate({"menarche": 88, "nomensage": None})

    for i in range (5, 26):
        assert not nv.validate({"menarche": 5, "nomensage": None})
    assert nv.errors == {'nomensage': ["('nomensage', ['null value not allowed']) for {'menarche': {'anyof': [{'min': 5, 'max': 25}, {'allowed': [99]}]}} - compatibility rule no: 0"]}
    assert not nv.validate({"menarche": 99, "nomensage": None})
    assert nv.errors == {'nomensage': ["('nomensage', ['null value not allowed']) for {'menarche': {'anyof': [{'min': 5, 'max': 25}, {'allowed': [99]}]}} - compatibility rule no: 0"]}
    assert not nv.validate({"menarche": 88, "nomensage": 10})
    assert nv.errors == {'nomensage': ["('nomensage', ['must be empty']) for {'menarche': {'nullable': True, 'anyof': [{'nullable': True, 'filled': False}, {'allowed': [88]}]}} - compatibility rule no: 1"]}
    assert not nv.validate({"menarche": None, "nomensage": 10})
    assert nv.errors == {'nomensage': ["('nomensage', ['must be empty']) for {'menarche': {'nullable': True, 'anyof': [{'nullable': True, 'filled': False}, {'allowed': [88]}]}} - compatibility rule no: 1"]}
