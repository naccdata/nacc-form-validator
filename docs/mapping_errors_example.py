#!/usr/bin/env python3
"""
Example of mapping nacc-form-validator errors to human-readable error messages.

The `errors` dict returned by `QualityCheck.validate_record` already contains
a generic message for each failed field, but many applications want to show
their own wording instead - sourced from wherever they maintain published
error text (a database, a flat file, an internal API, etc.), and possibly
keyed by a stable error code rather than the validator's internal rule name.

This example shows one simple way to do that:

  1. A `code_map` assigns a stable, publishable error code to each
     field/rule pair you care to override. This is kept separate from the
     validation schema itself, since schema rule names (e.g. "max",
     "compatibility") are implementation details of the validator, not
     identifiers meant to be shown to end users.
  2. An `ErrorMessageStore` looks up message text for those codes. Implement
     it against whatever system publishes your error message text, the same
     way `nacc_form_validator.datastore.Datastore` is implemented against
     whatever system stores previous records.
  3. `ErrorCodeMapper` ties the two together: for each top-level validation
     error, it resolves a code via `code_map`, looks up its message via the
     message store, and falls back to the validator's own default message
     if no custom code/message is available - so nothing is silently
     dropped. A "nullable" failure falls back to the same code as
     "required" for that field when one isn't published specifically for
     "nullable". Composite rules (e.g. "compatibility", "temporalrules")
     can define more than one condition for a field, so their entry in
     `code_map` is a list of `{"index": ..., "code": ...}` checks instead
     of a single code, matched against the index of the condition that
     actually failed.

Usage:

    python3 mapping_errors_example.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from nacc_form_validator.quality_check import QualityCheck

DEFAULT_ERROR_CODE = "qc-error"
NULLABLE_RULE = "nullable"
REQUIRED_RULE = "required"
COMPOSITE_RULES = {"compatibility", "temporalrules", "compute_gds"}


@dataclass
class MappedError:
    """A single human-readable error for one field in a validated record."""

    error_code: str
    field: str
    value: str
    message: str
    ptid: Optional[str]
    visitnum: Optional[str]
    visitdate: Optional[str]


class ErrorMessageStore(ABC):
    """Looks up published error message text by error code.

    Implement this against whatever system publishes your error message
    text - a CSV file, a database table, an internal API - the same way
    you would implement `nacc_form_validator.datastore.Datastore` against
    whatever system stores previous records.
    """

    @abstractmethod
    def get_messages(self, error_codes: List[str]) -> Dict[str, str]:
        """Returns message text for the given codes, keyed by code.

        Codes with no published message are simply omitted from the result.
        """


class InMemoryErrorMessageStore(ErrorMessageStore):
    """Minimal ErrorMessageStore backed by a plain dict.

    A real implementation would query a database, read a file, or call an
    internal API instead of looking up an in-memory dict.
    """

    def __init__(self, messages: Dict[str, str]) -> None:
        self.__messages = messages

    def get_messages(self, error_codes: List[str]) -> Dict[str, str]:
        return {code: self.__messages[code] for code in error_codes if code in self.__messages}


class ErrorCodeMapper:
    """Wraps QualityCheck's raw validation output and turns it into a list
    of human-readable errors.

    Only top-level errors are mapped - compound rules like "anyof"/"allof"
    also report a sub-error for each branch they tried, nested under the
    same field, and those are skipped since the compound rule itself is
    already reported as its own top-level error for the field.

    A "nullable" failure (the field was present but null) falls back to the
    "required" code for the same field when no code is published for
    "nullable" specifically, since both mean the field is missing a value.

    Some custom NACC rules (`COMPOSITE_RULES`: "compatibility",
    "temporalrules", "compute_gds") let a field define more than one
    condition to check, so a single rule failure needs to be resolved to
    one of several possible codes. For these rules, `code_map[field][rule]`
    is a list of `{"index": ..., "code": ...}` checks rather than a single
    code string, and `error.info[0]` gives the index of the condition that
    actually failed.
    """

    def __init__(
        self,
        *,
        input_data: Dict[str, str],
        code_map: Dict[str, Dict[str, Any]],
        message_store: ErrorMessageStore,
        ptid_field: str = "ptid",
        visitnum_field: str = "visitnum",
        visitdate_field: str = "visitdate",
    ) -> None:
        """
        Args:
            input_data: the record that was validated
            code_map: field -> rule name -> stable, publishable error code.
                For a rule in `COMPOSITE_RULES`, the value is instead a list
                of `{"index": ..., "code": ...}` checks, one per condition
                the rule defines for that field.
            message_store: looks up message text for a given error code
            ptid_field/visitnum_field/visitdate_field: field names to pull
                record-identifying info from; these vary by form/module
        """
        self.__input_data = input_data
        self.__code_map = code_map
        self.__message_store = message_store
        self.__ptid_field = ptid_field
        self.__visitnum_field = visitnum_field
        self.__visitdate_field = visitdate_field

    def map_errors(
        self, error_tree: Any, default_errors: Dict[str, List[str]]
    ) -> List[MappedError]:
        """Builds a list of human-readable errors from validator output.

        Args:
            error_tree: the `error_tree` returned by `QualityCheck.validate_record`
            default_errors: the `errors` dict returned by the same call, used
                as a fallback when no published message is available

        Returns:
            One `MappedError` per validation error encountered
        """
        codes_by_field: Dict[str, List[str]] = {}
        for field, node in error_tree.descendants.items():
            field_codes = self.__code_map.get(field, {})
            codes = []
            for error in node.errors:
                # Only map top-level errors - skip sub-errors nested under a
                # compound rule (e.g. anyof, allof), which is itself already
                # reported as a top-level error for the field.
                if error.rule != error.schema_path[1]:
                    continue

                rule = error.rule
                if (
                    rule == NULLABLE_RULE
                    and rule not in field_codes
                    and REQUIRED_RULE in field_codes
                ):
                    field_codes[rule] = field_codes[REQUIRED_RULE]

                if rule not in field_codes:
                    continue

                if rule in COMPOSITE_RULES:
                    code = self.__resolve_composite_code(field_codes[rule], error)
                    if code is not None:
                        codes.append(code)
                else:
                    codes.append(field_codes[rule])

            codes_by_field[field] = codes

        all_codes = [c for codes in codes_by_field.values() for c in codes]
        messages_by_code = self.__message_store.get_messages(all_codes)

        mapped: List[MappedError] = []
        for field, err_list in default_errors.items():
            value = str(self.__input_data.get(field, ""))
            codes = codes_by_field.get(field, [])
            messages = [(c, messages_by_code[c]) for c in codes if c in messages_by_code]

            if not messages:
                # No custom code/message available - fall back to the
                # validator's own default message(s) so nothing is dropped.
                messages = [(DEFAULT_ERROR_CODE, msg) for msg in err_list]

            for error_code, message in messages:
                mapped.append(
                    MappedError(
                        error_code=error_code,
                        field=field,
                        value=value,
                        message=message,
                        ptid=self.__input_data.get(self.__ptid_field),
                        visitnum=self.__input_data.get(self.__visitnum_field),
                        visitdate=self.__input_data.get(self.__visitdate_field),
                    )
                )

        return mapped

    @staticmethod
    def __resolve_composite_code(checks: List[Dict[str, Any]], error: Any) -> Optional[str]:
        """Resolves the code for a composite-rule failure.

        `error.info[0]` is the index of the condition (within the rule's own
        list of conditions) that actually failed; match it against each
        check's "index" to find the corresponding published code.
        """
        rule_index = error.info[0]
        for check in checks:
            if check["index"] == rule_index:
                return check["code"]
        return None


def main() -> None:
    # 1. The validation schema - normally loaded from wherever your rule
    #    definitions are stored (a file, a database, a remote API, ...).
    schema = {
        "ptid": {"type": "string", "required": True},
        "visitnum": {"type": "integer", "required": True},
        "visitdate": {"type": "string", "required": True},
        "age": {"type": "integer", "required": True, "min": 0, "max": 120},
        "sex": {"type": "integer", "required": True},
        "country": {"type": "string", "required": True},
        "state": {
            "type": "string",
            "nullable": True,
            "compatibility": [
                {
                    "index": 0,
                    "if": {"country": {"allowed": ["US"]}},
                    "then": {"state": {"empty": False}},
                }
            ],
        },
    }

    # 2. Stable, publishable codes for the field/rule combinations a schema
    #    author cares to give a custom message. Fields/rules left out here
    #    simply fall back to the validator's default message. "sex" only
    #    publishes a code for "required" - a null "sex" value below still
    #    resolves to it via the nullable -> required fallback. "state"
    #    publishes a code for condition 0 of its "compatibility" rule.
    code_map = {
        "age": {"max": "UDS-AGE-001", "min": "UDS-AGE-002"},
        "sex": {"required": "UDS-SEX-001"},
        "state": {"compatibility": [{"index": 0, "code": "UDS-STATE-001"}]},
    }

    # 3. Published error message text - normally loaded the same way, from
    #    wherever your organization maintains it.
    message_store = InMemoryErrorMessageStore(
        {
            "UDS-AGE-001": "Age must not be greater than 120.",
            "UDS-AGE-002": "Age must not be negative.",
            "UDS-SEX-001": "Sex must be provided.",
            "UDS-STATE-001": "State is required when country is US.",
        }
    )

    record = {
        "ptid": "PatientID1",
        "visitnum": 3,
        "visitdate": "2025-01-01",
        "age": 130,
        "sex": None,
        "country": "US",
        "state": "",
    }

    qc = QualityCheck("ptid", schema, strict=True, datastore=None)
    passed, sys_failure, errors, error_tree = qc.validate_record(record)

    if not passed and not sys_failure:
        mapper = ErrorCodeMapper(
            input_data=record, code_map=code_map, message_store=message_store
        )
        for mapped_error in mapper.map_errors(error_tree, errors):
            print(mapped_error)
            # MappedError(error_code='UDS-AGE-001', field='age', value='130',
            #     message='Age must not be greater than 120.', ptid='PatientID1',
            #     visitnum=3, visitdate='2025-01-01')
            # MappedError(error_code='UDS-SEX-001', field='sex', value='None',
            #     message='Sex must be provided.', ptid='PatientID1',
            #     visitnum=3, visitdate='2025-01-01')
            # MappedError(error_code='UDS-STATE-001', field='state', value='',
            #     message='State is required when country is US.',
            #     ptid='PatientID1', visitnum=3, visitdate='2025-01-01')


if __name__ == "__main__":
    main()
