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
    """ Run the validation on the provided schema, and checks that the expected result/errors are returned """
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
    """ Test enrollment form on a simple case - enrlbirthyr is required so the second record fails """
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
            "enrlbirthyr": None,  # required so will cause failure
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

def test_enrollment_form_all_fail():
    """ Test enrollment form on everything (or as much as we can have) failing """
    input_records = [
        {
            "adcid": -1,
            "frmdate_enrl": "invalid date",
            "enrltype": 3,
            "enrlbirthmo": 15,
            "enrlbirthyr": 1700,
            "enrleduc": 80,
            "guidavail": 3,
            "guid": 5,
            "prevenrl": 10,
            "oldadcid": -1,
            "ptidconf": "dummyptid2",
            "should_pass": False
        }
    ]

    expected_errors = [{
        'adcid': ['unallowed value -1'],
        'enrlbirthmo': ['max value is 12'],
        'enrlbirthyr': ['min value is 1850'],
        'enrleduc': ['no definitions validate',{'anyof definition 0': ['max value is 36'], 'anyof definition 1': ['unallowed value 80']}],
        'enrlgenman': ['error in formula evaluation - value None does not satisfy the specified formula'],
        'enrltype': ['unallowed value 3'],
        'frmdate_enrl': ['min date/year comparison error - Unknown string format: invalid date', "value does not match regex '(^(0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])[-/](\\d{4})$)|(^(\\d{4})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])$)'"],
        'guidavail': ['unallowed value 3'],
        'oldadcid': ['unallowed value -1', 'error in formula evaluation - value -1 does not satisfy the specified formula'],
        'prevenrl': ['unallowed value 10'],
        'ptid': ['required field'],
        'ptidconf': ['error in formula evaluation - value dummyptid2 does not satisfy the specified formula']
    }]
    run_validation('enrollment_rules.json',
                   input_records,
                   expected_errors)
