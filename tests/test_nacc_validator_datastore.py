"""
Tests the NACCValidator (from nacc_validator.py) when a datastore is required, e.g. temporal rules
Creates a dummy datastore for simple testing
"""
import copy
import pytest

from nacc_form_validator.nacc_validator import NACCValidator, CustomErrorHandler
from nacc_form_validator.datastore import Datastore


class CustomDatastore(Datastore):
    """Class to represent the datastore (or warehouse) where previous
    records stored
    """

    def __init__(self, pk_field: str, orderby: str) -> None:
        self.__db = {
            'PatientID1': [
                {
                    "visit_num": 1,
                    "taxes": 8,
                    "birthyr": 1950,
                    "birthmo": None
                },
                {
                    "visit_num": 3,
                    "taxes": 0,
                    "birthyr": 1950,
                    "birthmo": 6
                }
            ]
        }

        # dummy rxcui mapping for testing
        self.__valid_rxcui = list(range(50))

        super().__init__(pk_field, orderby)

    def get_previous_record(self, current_record: dict[str, str]) -> dict[str, str] | None:
        """
        See where current record would fit in the sorted record and return the previous record.
        Assumes the current record does NOT exist already in the database.
        Making a deep copy since we don't actually want to modify the record in this method
        """
        key = current_record[self.pk_field]
        if key not in self.__db:
            return None

        sorted_record = copy.deepcopy(self.__db[key])
        sorted_record.append(current_record)
        sorted_record.sort(key=lambda record: record[self.orderby])

        index = sorted_record.index(current_record)
        return sorted_record[index - 1] if index != 0 else None

    def get_previous_nonempty_record(self, current_record: dict[str, str], field: str) -> dict[str, str] | None:
        """
        Grabs the previous record where field is not empty
        """
        key = current_record[self.pk_field]
        if key not in self.__db:
            return None

        sorted_record = [x for x in copy.deepcopy(self.__db[key]) if x.get(field, None)]
        sorted_record.append(current_record)
        sorted_record.sort(key=lambda record: record[self.orderby])

        index = sorted_record.index(current_record)
        return sorted_record[index - 1] if index != 0 else None

    def is_valid_rxcui(self, drugid: int) -> bool:
        """ For RXCUI testing """
        return drugid in self.__valid_rxcui


def create_nacc_validator_with_ds(schema: dict[str, object], pk_field: str, orderby: str) -> NACCValidator:
    """ Creates a generic NACCValidtor with the above CustomDataStore """
    nv = NACCValidator(schema,
                       allow_unknown=False,
                       error_handler=CustomErrorHandler(schema))

    nv.primary_key = pk_field
    nv.datastore = CustomDatastore(pk_field, orderby)
    return nv

@pytest.fixture
def schema():
    return {
        "patient_id": {"type": "string"},
        "visit_num": {"type": "integer"},
        "taxes": {
            "type": "integer",
            "temporalrules": [
                    {
                        "index": 0,
                        "previous": {
                            "taxes": {"allowed": [0]}
                        },
                        "current": {
                            "taxes": {"forbidden": [8]}
                        }
                    }
            ]
        }
    }

def test_temporal_check(schema):
    """ Temporal test check - this is basically a more involved version of the example provided in docs/index.md """
    nv = create_nacc_validator_with_ds(schema, 'patient_id', 'visit_num')

    assert nv.validate({'patient_id': 'PatientID1',
                       'visit_num': 4, 'taxes': 1})
    assert not nv.validate(
        {'patient_id': 'PatientID1', 'visit_num': 4, 'taxes': 8})
    assert nv.errors == {'taxes': [
        "('taxes', ['unallowed value 8']) in current visit for {'taxes': {'allowed': [0]}} in previous visit - temporal rule no: 0"]}

def test_temporal_check_no_prev_visit(schema):
    """ Temporal test check when there are no previous visits (e.g. before visit 0) """
    nv = create_nacc_validator_with_ds(schema, 'patient_id', 'visit_num')

    assert not nv.validate(
        {'patient_id': 'PatientID1', 'visit_num': 0, 'taxes': 1})
    assert nv.errors == {'taxes': [
        'failed to retrieve the previous visit, cannot proceed with validation']}

def test_compare_with_previous_record():
    """ Test compare_with previous record """
    schema = {
        "patient_id": {"type": "string"},
        "visit_num": {"type": "integer"},
        "birthyr": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "previous_record"
            }
        }
    }

    nv = create_nacc_validator_with_ds(schema, 'patient_id', 'visit_num')
    assert nv.validate({'patient_id': 'PatientID1', 'visit_num': 4, 'birthyr': 1950})

    assert not nv.validate({'patient_id': 'PatientID1', 'visit_num': 4, 'birthyr': 2000})
    assert nv.errors == {'birthyr': ["input value doesn't satisfy the condition birthyr == previous_record"]}

    nv.reset_record_cache()
    assert nv.validate({'patient_id': 'PatientID1', 'visit_num': 2, 'birthyr': 1950})

def test_compare_with_previous_nonempty_record():
    """ Test compare_with previous nonempty record """
    schema = {
        "patient_id": {"type": "string"},
        "visit_num": {"type": "integer"},
        "birthmo": {
            "type": "integer",
            "compare_with": {
                "comparator": "==",
                "base": "previous_record",
                "ignore_empty": True
            }
        }
    }

    nv = create_nacc_validator_with_ds(schema, 'patient_id', 'visit_num')
    assert nv.validate({'patient_id': 'PatientID1', 'visit_num': 4, 'birthmo': 6})

    nv.reset_record_cache()
    assert not nv.validate({'patient_id': 'PatientID1', 'visit_num': 2, 'birthmo': 6})
    assert nv.errors == {'birthmo': ['failed to retrieve record for previous visit, cannot proceed with validation birthmo == previous_record']}

def test_check_with_rxnorm():
    """ Test checking drugID is a valid RXCUI """
    schema = {
        "drug": {
            "type": "integer",
            "check_with": "rxnorm"
        }
    }

    nv = create_nacc_validator_with_ds(schema, 'patient_id', 'visit_num')

    for i in range(50):
        assert nv.validate({"drug": i})

    assert not nv.validate({"drug": -1})
    assert nv.errors == {'drug': ['Drug ID -1 is not a valid RXCUI']}
    assert not nv.validate({"drug": 100})
    assert nv.errors == {'drug': ['Drug ID 100 is not a valid RXCUI']}

def test_check_with_rxnorm():
    """ Test checking drugID is a valid RXCUI """
    schema = {
        "drug": {
            "nullable": True,
            "type": "integer",
            "check_with": "rxnorm"
        }
    }

    nv = create_nacc_validator_with_ds(schema, 'patient_id', 'visit_num')

    # 0 and None are okay
    assert nv.validate({"drug": 0})
    assert nv.validate({"drug": None})

    for i in range(50):
        assert nv.validate({"drug": i})

    assert not nv.validate({"drug": -1})
    assert nv.errors == {'drug': ['Drug ID -1 is not a valid RXCUI']}
    assert not nv.validate({"drug": 100})
    assert nv.errors == {'drug': ['Drug ID 100 is not a valid RXCUI']}
