"""Utility/helper methods and fixtures used for testing."""

import pytest

from nacc_form_validator.errors import CustomErrorHandler
from nacc_form_validator.nacc_validator import NACCValidator


@pytest.fixture(scope="session")
def create_nacc_validator():

    def _create_nacc_validator(schema: dict[str, object]) -> NACCValidator:
        """Creates a NACCValidator with the provided schema (and no
        datastore)"""
        return NACCValidator(schema,
                             allow_unknown=False,
                             error_handler=CustomErrorHandler(schema))

    return _create_nacc_validator


@pytest.fixture
def nv(create_nacc_validator):
    """Returns a dummy QC with all data kinds of data types/rules to use for
    general testing."""
    schema = {
        "dummy_int": {
            "nullable": True,
            "type": "integer"
        },
        "dummy_str": {
            "nullable": True,
            "type": "string"
        },
        "dummy_float": {
            "nullable": True,
            "type": "float"
        },
        "dummy_boolean": {
            "nullable": True,
            "type": "boolean"
        },
        "dummy_date": {
            "nullable": True,
            "type": "date",
            "max": 3000
        },
        "dummy_datetime": {
            "nullable": True,
            "type": "datetime"
        },
    }

    return create_nacc_validator(schema)


@pytest.fixture(scope="session")
def date_constraint():
    """MM/DD/YYYY or YYYY/MM/DD."""
    return ("(^(0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])[-/](\\d{4})$)|"
    + "(^(\\d{4})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])$)")
