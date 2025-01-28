"""Tests the custom function _score_variables rule."""
import pytest


@pytest.fixture(scope='function')
def base_schema():
    """Base schema for tests to use."""
    return {
        'total': {
            'type': 'integer',
            'required': True,
            'function': {
                'name': 'score_variables',
                'args': {
                    'mode': 'correct',
                    'scoring_key': {
                        'val1': 1,
                        'val2': 2,
                        'val3': 3
                    },
                    'logic': {
                        'formula': {
                            '==': [{
                                'var': 'total'
                            }, {
                                'var': '__total_sum'
                            }]
                        }
                    }
                }
            }
        },
        'val1': {
            'type': 'integer',
            'nullable': True
        },
        'val2': {
            'type': 'integer',
            'nullable': True
        },
        'val3': {
            'type': 'integer',
            'nullable': True
        }
    }


def test_score_variables_total_correct(create_nacc_validator, base_schema):
    """Test score variables with simple comparison against the total sum
    counting correct variables."""
    nv = create_nacc_validator(base_schema)

    # valid cases
    assert nv.validate({'total': 3, 'val1': 1, 'val2': 2, 'val3': 3})
    assert nv.validate({'total': 1, 'val1': 5, 'val2': 2, 'val3': -7})
    assert nv.validate({'total': 0, 'val1': 5, 'val2': 0, 'val3': -7})

    # valid, will skip validation if any variables in scoring key is null
    assert nv.validate({'total': 5})
    assert nv.validate({'total': 5, 'val1': 5, 'val3': 4})

    # invalid cases
    assert not nv.validate({'total': 10, 'val1': 1, 'val2': 2, 'val3': 3})
    assert nv.errors == {'total': ["Field does not match expected score: 10"]}
    assert not nv.validate({'total': 9, 'val1': 5, 'val2': 2, 'val3': -7})
    assert nv.errors == {'total': ["Field does not match expected score: 9"]}
    assert not nv.validate({'total': 8, 'val1': 5, 'val2': 0, 'val3': -7})
    assert nv.errors == {'total': ["Field does not match expected score: 8"]}


def test_score_variables_total_incorrect(create_nacc_validator, base_schema):
    """Test score variables with simple comparison against the total sum
    counting incorrect variables."""
    base_schema['total']['function']['args']['mode'] = 'incorrect'
    nv = create_nacc_validator(base_schema)

    # valid cases
    assert nv.validate({'total': 3, 'val1': 3, 'val2': 1, 'val3': 2})
    assert nv.validate({'total': 1, 'val1': 3, 'val2': 2, 'val3': 3})
    assert nv.validate({'total': 0, 'val1': 1, 'val2': 2, 'val3': 3})

    # valid, will skip validation if any variables in scoring key is null
    assert nv.validate({'total': 5})
    assert nv.validate({'total': 5, 'val1': 5, 'val3': 4})

    # invalid cases
    assert not nv.validate({'total': 3, 'val1': 1, 'val2': 2, 'val3': 3})
    assert nv.errors == {'total': ["Field does not match expected score: 3"]}
    assert not nv.validate({'total': 1, 'val1': 5, 'val2': 2, 'val3': -7})
    assert nv.errors == {'total': ["Field does not match expected score: 1"]}
    assert not nv.validate({'total': 0, 'val1': 5, 'val2': 0, 'val3': -7})
    assert nv.errors == {'total': ["Field does not match expected score: 0"]}


def test_score_variables_total_incorrect_subtraction(create_nacc_validator,
                                                     base_schema):
    """Test score variables with comparison involving more involved logic
    formula counting incorrect values."""
    base_schema['total']['function']['args']['mode'] = 'incorrect'
    base_schema['total']['function']['args']['logic'] = {
        'formula': {
            '==': [{
                'var': 'total'
            }, {
                '-': [5, {
                    'var': '__total_sum'
                }]
            }]
        }
    }
    nv = create_nacc_validator(base_schema)

    # valid cases
    assert nv.validate({'total': 2, 'val1': 3, 'val2': 1, 'val3': 2})
    assert nv.validate({'total': 4, 'val1': 3, 'val2': 2, 'val3': 3})
    assert nv.validate({'total': 5, 'val1': 1, 'val2': 2, 'val3': 3})

    # valid, will skip validation if any variables in scoring key is null
    assert nv.validate({'total': 5})
    assert nv.validate({'total': 5, 'val1': 5, 'val3': 4})

    # invalid cases
    assert not nv.validate({'total': 3, 'val1': 1, 'val2': 2, 'val3': 3})
    assert nv.errors == {'total': ["Field does not match expected score: 3"]}
    assert not nv.validate({'total': 1, 'val1': 5, 'val2': 2, 'val3': -7})
    assert nv.errors == {'total': ["Field does not match expected score: 1"]}
    assert not nv.validate({'total': 0, 'val1': 5, 'val2': 0, 'val3': -7})
    assert nv.errors == {'total': ["Field does not match expected score: 0"]}
