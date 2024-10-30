"""
Tests the custom compute_gds rule (_validate_compute_gds).
"""
import pytest
from utils import create_nacc_validator


@pytest.fixture
def gds_nv():
    """ Create a validator with GDS fields for testing """
    schema = {
        "satis": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "dropact": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "empty": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "bored": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "spirits": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "afraid": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "happy": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "helpless": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "stayhome": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "memprob": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "wondrful": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "wrthless": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "energy": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "hopeless": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "better": {
            "required": True,
            "type": "integer",
            "allowed": [0, 1, 9]
        },
        "gds": {
            "required": True,
            "type": "integer",
            "anyof": [
                {
                    "min": 0,
                    "max": 15
                },
                {
                    "allowed": [
                        88
                    ]
                }
            ],
            "compute_gds": [
                "satis",
                "dropact",
                "empty",
                "bored",
                "spirits",
                "afraid",
                "happy",
                "helpless",
                "stayhome",
                "memprob",
                "wondrful",
                "wrthless",
                "energy",
                "hopeless",
                "better"
            ]
        },
        "nogds": {
            "nullable": True,
            "type": "integer",
            "allowed": [1]
        }
    }

    return create_nacc_validator(schema)

@pytest.fixture
def gds_record():
    """ Generic valid GDS record to use for testing """
    return {
        "satis": 1,
        "dropact": 1,
        "empty": 1,
        "bored": 1,
        "spirits": 1,
        "afraid": 1,
        "happy": 1,
        "helpless": 1,
        "stayhome": 1,
        "memprob": 1,
        "wondrful": 1,
        "wrthless": 1,
        "energy": 1,
        "hopeless": 1,
        "better": 1,
        "gds": 15,
        "nogds": None
    }

def test_compute_gds_all_answered(gds_nv, gds_record):
    """ Test compute_gds when all fields were answered so gds total must match, basically rule 3 """
    assert gds_nv.validate(gds_record)

    for k in gds_record:
        if k not in ['nogds', 'gds']:
            gds_record[k] = 0
            gds_record['gds'] -= 1
            assert gds_nv.validate(gds_record)

    # invalid, test wrong gds value
    gds_record.update({'gds': 5})
    assert not gds_nv.validate(gds_record)
    assert gds_nv.errors == {'gds': ['incorrect total GDS score 5, expected value 0 - GDS rule no: 2']}

def test_compute_gds_nogds_is_1(gds_nv, gds_record):
    """ Test compute_gds when `nogds` is 1 """
    # if NOGDS = 1 then GDS must be 88
    gds_record.update({'nogds': 1})
    assert not gds_nv.validate(gds_record)
    assert gds_nv.errors == {'gds': ['If GDS not attempted (nogds=1), there cannot be >=12 questions with valid scores - GDS rule no: 1', 'If GDS not attempted (nogds=1), total GDS score should be 88 - GDS rule no: 0']}

    # if NOGDS = 1 then there cannot be >= 12 questions with valid scores (0 or 1)
    gds_record.update({'gds': 88})
    assert not gds_nv.validate(gds_record)
    assert gds_nv.errors == {'gds': ['If GDS not attempted (nogds=1), there cannot be >=12 questions with valid scores - GDS rule no: 1']}

    # set fields to 9 to test the limit < 12 limit
    count = 0
    for k in gds_record:
        if k not in ['nogds', 'gds']:
            gds_record[k] = 9
            count += 1
            if count < 3:
                assert not gds_nv.validate(gds_record)
                assert gds_nv.errors == {'gds': ['If GDS not attempted (nogds=1), there cannot be >=12 questions with valid scores - GDS rule no: 1']}
            else:
                gds_nv.validate(gds_record)

def test_compute_gds_nogds_is_blank(gds_nv, gds_record):
    """ Test compute_gds when `nogds` is blank """
    # if NOGDS is blank then there must be at least 12 questions with valid scores
    # if up to 3 of the 15 items are unanswered, then GDS is equal to the scoring algorithm
    count = 0
    for k in gds_record:
        if k not in ['nogds', 'gds']:
            gds_record[k] = 9
            count += 1
            if count <= 3:
                assert gds_nv.validate(gds_record)  # when all are 1, scoring algorithm will compute all to be 15
            else:
                assert not gds_nv.validate(gds_record)
                assert gds_nv.errors == {'gds': ['If GDS attempted (nogds=blank), at least 12 questions need to have valid scores - GDS rule no: 4']}

def test_compute_gds_scoring_algorithm(gds_nv):
    """ Test the GDS scoring algorithm specifically """
    # this record has 2 unanswered (=9) and a total score of 5, so expected value of GDS is 6.25 (rounded down to 6)
    record = {
        "satis": 9,
        "dropact": 9,
        "empty": 1,
        "bored": 1,
        "spirits": 1,
        "afraid": 1,
        "happy": 1,
        "helpless": 0,
        "stayhome": 0,
        "memprob": 0,
        "wondrful": 0,
        "wrthless": 0,
        "energy": 0,
        "hopeless": 0,
        "better": 0,
        "gds": 6,
        "nogds": None
    }

    assert gds_nv.validate(record)

    record['gds'] = 13
    assert not gds_nv.validate(record)
    assert gds_nv.errors ==  {'gds': ['incorrect partial GDS score 13, expected value 6 - GDS rule no: 3']}
