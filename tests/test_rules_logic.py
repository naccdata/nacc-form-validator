"""
Tests the custom logic rule (_validate_logic).
"""
from utils import create_nacc_validator


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

def test_logic_and():
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
