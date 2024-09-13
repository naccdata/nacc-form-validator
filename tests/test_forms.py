"""
Regression tests for completed forms themselves
"""
import json
import pytest

from pathlib import Path
from nacc_form_validator import QualityCheck

NACC_RULES_JSONS = Path(__file__).resolve().parent / '..' / 'docs' / 'nacc-rules'
ENROLLV1_FORMS = NACC_RULES_JSONS / 'ENROLLV1'


def run_validation(rules_json: str,
                   input_records: list[dict[str, object]],
                   expected_errors: list[dict[str, object]],
                   pk_name: str = None,
                   datastore: object = None):

    with (ENROLLV1_FORMS / rules_json).open('r') as fh:
        schema = json.load(fh)

    qc = QualityCheck(pk_name, schema, strict=True, datastore=datastore)
    all_errors = []

    for record in input_records:
        should_pass = record.pop('should_pass')
        passed, _, errors, _ = qc.validate_record(record)
        assert passed == should_pass

        if not passed:
            all_errors.append(errors)

    assert all_errors == expected_errors

def test_enrollment_form():
    input_records = [
        {
            "adcid": 0,
            "ptid": "dummyptid",
            "frmdate_enrl": "05-17-2024",
            "enrltype": 1,
            "enrlbirthmo": 1,
            "enrlbirthyr": "2000",
            "enrleduc": 0,
            "enrlgenman": 1,
            "guidavail": 0,
            "prevenrl": 0,
            "ptidconf": "dummyptid",
            "should_pass": True
        },
        {
            "adcid": 0,
            "ptid": "dummyptid",
            "frmdate_enrl": "05-17-2024",
            "enrltype": 1,
            "enrlbirthmo": 1,
            "enrlbirthyr": None,
            "enrleduc": 0,
            "enrlgenman": 1,
            "guidavail": 0,
            "prevenrl": 0,
            "ptidconf": "dummyptid",
            "should_pass": False
        }
    ]

    expected_errors = [{'enrlbirthyr': ['null value not allowed']}]
    run_validation('enrollment_rules.json',
                   input_records,
                   expected_errors)
