"""
Tests the NACCValidator (from nacc_validator.py) when a datastore is required, e.g. temporal rules
Creates a dummy datastore for simple testing
"""
import copy

from nacc_form_validator.nacc_validator import NACCValidator, CustomErrorHandler
from nacc_form_validator.datastore import Datastore


class CustomDatastore(Datastore):

    def __init__(self) -> None:
        self.__db = {
            'PatientID1': [
                {
                    "visit_num": 1,
                    "taxes": 8
                },
                {
                    "visit_num": 3,
                    "taxes": 0
                }
            ]
        }

    def get_previous_instance(self, orderby: str, pk_field: str, current_ins: dict[str, str]) -> dict[str, str] | None:
        """
        See where this record would fit in the sorted record and return the previous instance
        Making a deep copy since we don't actually want to modify the record in this method
        """
        key = current_ins[pk_field]
        if key not in self.__db:
            return None
        
        sorted_record = copy.deepcopy(self.__db[key])
        sorted_record.append(current_ins)
        sorted_record.sort(key=lambda record: record[orderby])

        index = sorted_record.index(current_ins)
        return sorted_record[index - 1] if index != 0 else None


def create_nacc_validator_with_ds(schema: dict[str, object]) -> NACCValidator:
    """ Creates a generic NACCValidtor with the above CustomDataStore """
    nv = NACCValidator(schema,
                       allow_unknown=False,
                       error_handler=CustomErrorHandler(schema))

    nv.primary_key = 'patient_id'
    nv.datastore = CustomDatastore()
    return nv


def test_temporal_check():
    """ Temporal test check - this is basically a more involved version of the example provided in docs/index.md, namely tests when 
    validating a record that sits inbetween or before existing records in the DS """
    schema = {
        "patient_id": {"type": "string"},
        "visit_num": {"type": "integer"},
        "taxes": {
            "type": "integer",
            "temporalrules": {
                "orderby": "visit_num",
                "constraints": [
                    {
                        "previous": {"allowed": [0]},
                        "current": {"forbidden": [8]}
                    }
                ]
            }
        }
    }

    nv = create_nacc_validator_with_ds(schema)

    assert nv.validate({'patient_id': 'PatientID1', 'visit_num': 4, 'taxes': 1})
    assert not nv.validate({'patient_id': 'PatientID1', 'visit_num': 4, 'taxes': 8})
    assert nv.errors == {'taxes': ["('taxes', ['unallowed value 8']) in current visit for {'allowed': [0]} in previous visit - temporal rule no: 1"]}

    nv.reset_record_cache()
    assert not nv.validate({'patient_id': 'PatientID1', 'visit_num': 0, 'taxes': 1})
    assert nv.errors == {'taxes': ['failed to retrieve the previous visit, cannot proceed with validation']}
