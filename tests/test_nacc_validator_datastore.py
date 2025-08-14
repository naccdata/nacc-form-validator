"""Tests the NACCValidator (from nacc_validator.py) when a datastore is
required, e.g. temporal rules Creates a dummy datastore for simple testing."""

import copy
from typing import Any, Dict, List, Optional

import pytest

from nacc_form_validator.datastore import Datastore
from nacc_form_validator.errors import CustomErrorHandler
from nacc_form_validator.nacc_validator import NACCValidator


class CustomDatastore(Datastore):
    """Class to represent the datastore (or warehouse) where previous records
    stored."""

    def __init__(self, pk_field: str, orderby: str) -> None:
        self.__db = {
            "PatientID1": [
                {
                    "visit_num": 1,
                    "taxes": 8,
                    "birthyr": 1950,
                    "birthmo": None,
                    "birthdy": 27,
                },
                {
                    "visit_num": 3,
                    "taxes": 0,
                    "birthyr": 1950,
                    "birthmo": 6,
                    "birthdy": 9,
                },
            ]
        }

        # dummy rxcui mapping for testing
        self.__valid_rxcui = list(range(50))

        # dummy ADCIDs for testing
        self.__adcid = 0
        self.__valid_adcids = [0, 2, 5, 8, 10]

        super().__init__(pk_field, orderby)

    def get_previous_record(
            self, current_record: Dict[str, str]) -> Optional[Dict[str, str]]:
        """See where current record would fit in the sorted record and return
        the previous record.

        Assumes the current record does NOT exist already in the
        database. Making a deep copy since we don't actually want to
        modify the record in this method
        """
        key = current_record[self.pk_field]
        if key not in self.__db:
            return None

        sorted_record = copy.deepcopy(self.__db[key])
        sorted_record.append(current_record)
        sorted_record.sort(
            key=lambda record: record[self.orderby])  # type: ignore

        index = sorted_record.index(current_record)
        return sorted_record[index - 1] if index != 0 else None  # type: ignore

    def get_previous_nonempty_record(
            self, current_record: Dict[str, str],
            ignore_empty_fields: List[str]) -> Optional[Dict[str, str]]:
        """Grabs the previous record where field is not empty."""
        key = current_record[self.pk_field]
        if key not in self.__db:
            return None

        sorted_record = []
        for x in self.__db[key]:
            nonempty = True
            for f in ignore_empty_fields:
                if x.get(f, None) is None:  # type: ignore
                    nonempty = False
            if nonempty:
                sorted_record.append(x)

        sorted_record.append(current_record)
        sorted_record.sort(
            key=lambda record: record[self.orderby])  # type: ignore

        index = sorted_record.index(current_record)
        return sorted_record[index - 1] if index != 0 else None  # type: ignore

    def get_initial_record(
        self,
        current_record: Dict[str, Any],
        ignore_empty_fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Grabs the initial record."""
        key = current_record[self.pk_field]
        if key not in self.__db:
            return None

        if self.__db.get(key, None):
            return self.__db[key][0]  # type: ignore

        return None

    def is_valid_rxcui(self, drugid: int) -> bool:
        """For RXCUI testing."""
        return drugid in self.__valid_rxcui

    def is_valid_adcid(self, adcid: int, own: bool) -> bool:
        """For ADCID testing."""
        if own:
            return adcid == self.__adcid

        return adcid in self.__valid_adcids


def create_nacc_validator_with_ds(schema: Dict[str, object], pk_field: str,
                                  orderby: str) -> NACCValidator:
    """Creates a generic NACCValidtor with the above CustomDataStore."""
    nv = NACCValidator(schema,
                       allow_unknown=False,
                       error_handler=CustomErrorHandler(schema))

    nv.primary_key = pk_field
    nv.datastore = CustomDatastore(pk_field, orderby)
    return nv


@pytest.fixture
def schema():
    return {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "taxes": {
            "type":
            "integer",
            "temporalrules": [{
                "index": 0,
                "previous": {
                    "taxes": {
                        "allowed": [0]
                    }
                },
                "current": {
                    "taxes": {
                        "forbidden": [8]
                    }
                },
            }],
        },
    }


def test_temporal_check(schema):
    """Temporal test check - this is basically a more involved version of the
    example provided in docs/index.md.
    """
    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "taxes": 1
    })

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "taxes": 8
    })
    assert nv.errors == {
        "taxes": [
            "('taxes', ['unallowed value 8']) for if {'taxes': {'allowed': [0]}} "
            +
            "in previous visit then {'taxes': {'forbidden': [8]}} in current "
            + "visit - temporal rule no: 0"
        ]
    }


def test_temporal_check_swap_order(schema):
    """Test temporal check when the order of evaluation is swapped."""
    schema["taxes"]["temporalrules"][0]["swap_order"] = True
    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "taxes": 1
    })
    # since 8 fails the current condition, validation skipped
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "taxes": 8
    })

    nv.reset_record_cache()
    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 2,
        "taxes": 1
    })
    assert nv.errors == {
        "taxes": [
            "('taxes', ['unallowed value 8']) for if {'taxes': {'forbidden': [8]}} "
            +
            "in current visit then {'taxes': {'allowed': [0]}} in previous " +
            "visit - temporal rule no: 0"
        ]
    }


def test_temporal_check_no_prev_visit(schema):
    """Temporal test check when there are no previous visits (e.g. before visit
    0)"""
    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 0,
        "taxes": 1
    })
    assert nv.errors == {
        "taxes": [
            "failed to retrieve the previous visit, cannot proceed with validation"
        ]
    }


def test_temporal_check_previous_nonempty():
    """Temporal check where previous record is nonempty."""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "birthmo": {
            "type":
            "integer",
            "temporalrules": [{
                "index": 0,
                "ignore_empty": ["birthmo", "birthdy"],
                "previous": {
                    "birthmo": {
                        "nullable": False
                    },
                    "birthdy": {
                        "nullable": False
                    },
                },
                "current": {
                    "birthmo": {
                        "nullable": False
                    }
                },
            }],
        },
    }
    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthmo": 6
    })

    # if ignore_empty is set and we cannot find a record, pass through the validation
    nv.reset_record_cache()
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 2,
        "birthmo": 6
    })


def test_compare_with_previous_record():
    """Test compare_with previous record."""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "birthyr": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "birthyr",
                "previous_record": True,
            },
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthyr": 1950
    })

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthyr": 2000
    })
    assert nv.errors == {
        "birthyr": [
            "input value doesn't satisfy the condition " +
            "birthyr == birthyr (previous record)"
        ]
    }

    nv.reset_record_cache()
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 2,
        "birthyr": 1950
    })


def test_compare_with_previous_nonempty_record():
    """Test compare_with previous nonempty record."""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "birthmo": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "birthmo",
                "previous_record": True,
                "ignore_empty": True,
            },
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthmo": 6
    })

    # since ignore_empty = True, this will skip over validation in the previous
    # record not found
    nv.reset_record_cache()
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 2,
        "birthmo": 6
    })


def test_compare_with_previous_nonempty_record_not_allowed():
    """Test compare_with previous nonempty record but not ignoring empty."""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "birthmo": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "birthmo",
                "previous_record": True,
            },
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthmo": 6
    })

    # since ignore_empty = False, this is not allowed
    nv.reset_record_cache()
    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 2,
        "birthmo": 6
    })
    assert nv.errors == {
        "birthmo": [
            "failed to retrieve record for previous visit, cannot proceed with "
            + "validation birthmo == birthmo (previous record)"
        ]
    }


def test_compare_with_previous_different_variable():
    """Test compare_with previous record and a different variable name.

    This is identical to the test_compare_with_previous_record test just
    with different variables
    """
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "birthyear": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "birthyr",
                "previous_record": True,
            },
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthyear": 1950
    })

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthyear": 2000
    })
    assert nv.errors == {
        "birthyear": [
            "input value doesn't satisfy the condition " +
            "birthyear == birthyr (previous record)"
        ]
    }

    nv.reset_record_cache()
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 2,
        "birthyear": 1950
    })


def test_temporal_check_with_nested_compare_with_previous_record():
    """Test when compare_with previous_record nested inside a temporalrules."""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer"
        },
        "birthyr": {
            "type":
            "integer",
            "temporalrules": [{
                "index": 0,
                "previous": {
                    "birthyr": {
                        "forbidden": [-1]
                    }
                },
                "current": {
                    "birthyr": {
                        "compare_with": {
                            "comparator": "==",
                            "base": "birthyr",
                            "previous_record": True,
                        }
                    }
                },
            }],
        },
    }
    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")
    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthyr": 1950
    })

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 4,
        "birthyr": 1951
    })
    assert nv.errors == {
        "birthyr": [
            "('birthyr', [\"input value doesn't satisfy the condition " +
            "birthyr == birthyr (previous record)\"]) for " +
            "if {'birthyr': {'forbidden': [-1]}} in previous visit " +
            "then {'birthyr': {'compare_with': {'comparator': '==', " +
            "'base': 'birthyr', 'previous_record': True}}} in current visit " +
            "- temporal rule no: 0"
        ]
    }


def test_compare_with_initial_visit():
    """Compare with test check when requesting initial visit (visit_num ==
    1)"""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer",
        },
        "birthdy": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "birthdy",
                "initial_record": True,
            },
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 1,
        "birthdy": 27
    })

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 3,
        "birthdy": 30
    })

    assert nv.errors == {
        'birthdy': [
            "input value doesn't satisfy the condition " +
            "birthdy == birthdy (initial record)"
        ]
    }


def test_temporal_rule_initial_visit():
    """Temporal rule test check when requesting initial visit (visit_num ==
    1)"""
    schema = {
        "patient_id": {
            "type": "string"
        },
        "visit_num": {
            "type": "integer",
        },
        "birthdy": {
            "type":
            "integer",
            "temporalrules": [{
                "index": 0,
                "initial_record": True,
                "previous": {
                    "birthdy": {
                        "allowed": [27],
                    }
                },
                "current": {
                    "birthdy": {
                        "allowed": [30]
                    }
                },
            }],
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    assert nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 3,
        "birthdy": 30
    })

    assert not nv.validate({
        "patient_id": "PatientID1",
        "visit_num": 3,
        "birthdy": 27
    })

    assert nv.errors == {
        'birthdy': [
            "('birthdy', ['unallowed value 27']) for if {'birthdy': {'allowed': [27]}} "
            + "in initial visit then {'birthdy': {'allowed': [30]}} " +
            "in current visit - temporal rule no: 0"
        ]
    }


def test_check_with_rxnorm():
    """Test checking drugID is a valid RXCUI."""
    schema = {"drug": {"type": "integer", "check_with": "rxnorm"}}

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    for i in range(50):
        assert nv.validate({"drug": i})

    assert not nv.validate({"drug": -1})
    assert nv.errors == {"drug": ["Drug ID -1 is not a valid RXCUI"]}
    assert not nv.validate({"drug": 100})
    assert nv.errors == {"drug": ["Drug ID 100 is not a valid RXCUI"]}


def test_check_adcid():
    """Test checking provided ADCID is valid."""

    schema = {
        "adcid": {
            "type": "integer",
            "function": {
                "name": "check_adcid"
            }
        },
        "oldadcid": {
            "type": "integer",
            "function": {
                "name": "check_adcid",
                "args": {
                    "own": False
                }
            },
        },
    }

    nv = create_nacc_validator_with_ds(schema, "patient_id", "visit_num")

    assert nv.validate({"adcid": 0})
    assert nv.validate({"oldadcid": 10})
    assert not nv.validate({"adcid": 1})
    assert nv.errors == {
        "adcid": ["Provided ADCID 1 does not match your center's ADCID"]
    }
    assert not nv.validate({"oldadcid": 20})
    assert nv.errors == {
        "oldadcid": ["Provided ADCID 20 is not in the valid list of ADCIDs"]
    }
