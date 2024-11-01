"""
Tests the custom logic rule (_validate_logic).
"""
def test_logic_or(create_nacc_validator):
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
                        {"==": [1, {"var": "raceblack"}]}
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

    # invalid cases
    assert not nv.validate({'raceaian': None, 'raceasian': None, 'raceblack': None})
    assert nv.errors == {'raceaian': ['error in formula evaluation - value None does not satisfy the specified formula']}
    assert not nv.validate({'raceaian': None})
    assert nv.errors == {'raceaian': ['error in formula evaluation - value None does not satisfy the specified formula']}

def test_logic_and(create_nacc_validator):
    """ Test mathematical logic and case """
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
                    "and": [
                        {"==": [1, {"var": "raceaian"}]},
                        {"==": [1, {"var": "raceasian"}]},
                        {"==": [1, {"var": "raceblack"}]}
                    ]
                }
            }
        }
    }
    nv = create_nacc_validator(schema)

    # only valid case
    assert nv.validate({'raceaian': 1, 'raceasian': 1, 'raceblack': 1})

    # invalid cases
    assert not nv.validate({'raceaian': 1, 'raceasian': None, 'raceblack': None})
    assert nv.errors == {'raceaian': ['error in formula evaluation - value 1 does not satisfy the specified formula']}

def test_logic_or_equality_with_none(create_nacc_validator):
    """ Check logic can handle null values """
    schema = {
        "sib1yob": {"type": "integer", "nullable": True},
        "sib2yob": {"type": "integer", "nullable": True},
        "sib3yob": {"type": "integer", "nullable": True},
        "sib4yob": {"type": "integer", "nullable": True},
        "sib5yob": {"type": "integer", "nullable": True},
        "ftdsibby": {
            "type": "integer", "required": True,
            "logic": {
                "formula": {
                    "or": [
                        {
                            "<=": [{"var": "ftdsibby"}, {"var": "sib1yob"}]
                        },
                        {
                            "==": [{"var": "ftdsibby"}, {"var": "sib2yob"}]
                        },
                        {
                            "==": [{"var": "ftdsibby"}, {"var": "sib3yob"}]
                        },
                        {
                            "==": [{"var": "ftdsibby"}, {"var": "sib4yob"}]
                        },
                        {
                            "==": [{"var": "ftdsibby"}, {"var": "sib5yob"}]
                        }
                    ]
                }
            }
        }
    }
    nv = create_nacc_validator(schema)

    assert nv.validate({'ftdsibby': 2000, 'sib1yob': 2000})
    assert nv.validate({'ftdsibby': 2000, 'sib2yob': 2000})
    assert nv.validate({'ftdsibby': 2000, 'sib3yob': 2000})
    assert nv.validate({'ftdsibby': 2000, 'sib4yob': 2000})
    assert nv.validate({'ftdsibby': 2000, 'sib5yob': 2000})
    assert nv.validate({'ftdsibby': 2000, 'sib1yob': 1990 , 'sib2yob': 1991, 'sib3yob': 2000, 'sib4yob': 1993, 'sib5yob': 1994})
    assert nv.validate({'ftdsibby': 2000, 'sib1yob': None , 'sib2yob': None, 'sib3yob': 2000})

    assert not nv.validate({'ftdsibby': 2000, 'sib1yob': 1990 , 'sib2yob': 1991, 'sib3yob': 1992, 'sib4yob': 1993, 'sib5yob': 1994})
    assert nv.errors == {'ftdsibby': ['error in formula evaluation - value 2000 does not satisfy the specified formula']}
    assert not nv.validate({'ftdsibby': 2000, 'sib1yob': None , 'sib2yob': 1991, 'sib3yob': None, 'sib4yob': 1993, 'sib5yob': None})
    assert nv.errors == {'ftdsibby': ['error in formula evaluation - value 2000 does not satisfy the specified formula']}
    assert not nv.validate({'ftdsibby': 2000})
    assert nv.errors == {'ftdsibby': ['error in formula evaluation - value 2000 does not satisfy the specified formula']}

def test_logic_sum(create_nacc_validator):
    """ Test must equal a sum logic, which is a common rule """
    schema = {
        "var1": {"type": "integer"},  # important to note, additive logic does NOT support null values, so either
        "var2": {"type": "integer"},  # these need to be required (as done in this test), OR the logic needs
        "var3": {"type": "integer"},  # to be wrapped in a compatibility rule that first checks they're not null
        "total": {
            "type": "integer",
            "logic": {
                "formula": {
                    "==": [
                        {"var": "total"},
                        {
                            "+": [
                                {"var": "var1"},
                                {"var": "var2"},
                                {"var": "var3"}
                            ]
                        }
                    ]
                }
            }
        }
    }
    nv = create_nacc_validator(schema)

    assert nv.validate({"total": 10, "var1": 5, "var2": 3, "var3": 2})
    assert nv.validate({"total": 10, "var1": 10, "var2": 0, "var3": 0})
    assert nv.validate({"total": 10, "var1": 20, "var2": -5, "var3": -5})

    assert not nv.validate({"total": 9, "var1": 5, "var2": 3, "var3": 2})
    assert nv.errors == {'total': ['error in formula evaluation - value 9 does not satisfy the specified formula']}
