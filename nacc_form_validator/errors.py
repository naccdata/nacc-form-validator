"""Error-code and schema related constants."""

from typing import Mapping

from cerberus.errors import (
    BasicErrorHandler,
    ErrorDefinition,
    ErrorTree,
    ValidationError,
)


# pylint: disable=(too-few-public-methods)
class ErrorDefs:
    """Class to define custom errors."""

    # IMPORTANT - When adding a new error DON'T change the existing codes
    # Error codes are used to map b/w cerberus errors and NACC QC check codes
    # Cerberus uses bit 5 and bit 7 to mark specific error types
    # Check https://docs.python-cerberus.org/customize.html for more info
    CURR_DATE_MAX = ErrorDefinition(0x1000, "max")
    CURR_YEAR_MAX = ErrorDefinition(0x1001, "max")
    INVALID_DATE_MAX = ErrorDefinition(0x1002, "max")
    CURR_DATE_MIN = ErrorDefinition(0x1003, "min")
    CURR_YEAR_MIN = ErrorDefinition(0x1004, "min")
    INVALID_DATE_MIN = ErrorDefinition(0x1005, "min")
    FILLED_TRUE = ErrorDefinition(0x1006, "filled")
    FILLED_FALSE = ErrorDefinition(0x1007, "filled")
    COMPATIBILITY = ErrorDefinition(0x1008, "compatibility")
    COMPATIBILITY_ELSE = ErrorDefinition(0x1009, "compatibility")
    TEMPORAL = ErrorDefinition(0x2000, "temporalrules")
    NO_PRIMARY_KEY = ErrorDefinition(0x2001, "temporalrules")
    NO_PREV_VISIT = ErrorDefinition(0x2002, "temporalrules")
    FORMULA = ErrorDefinition(0x2003, "logic")
    CHECK_GDS_1 = ErrorDefinition(0x2004, "compute_gds")
    CHECK_GDS_2 = ErrorDefinition(0x2005, "compute_gds")
    CHECK_GDS_3 = ErrorDefinition(0x2006, "compute_gds")
    CHECK_GDS_4 = ErrorDefinition(0x2007, "compute_gds")
    COMPARE_WITH = ErrorDefinition(0x2008, "compare_with")
    COMPARE_WITH_PREV = ErrorDefinition(0x2009, "compare_with")
    RXNORM = ErrorDefinition(0x3000, "check_with")
    DATE_CONVERSION = ErrorDefinition(0x3001, 'compare_age')
    COMPARE_AGE = ErrorDefinition(0x3002, 'compare_age')
    COMPARE_AGE_INVALID_COMPARISON = ErrorDefinition(0x3003, 'compare_age')
    TEMPORAL_SWAPPED = ErrorDefinition(0x3004, 'temporalrules')


class CustomErrorHandler(BasicErrorHandler):
    """Class to provide custom error messages."""

    def __init__(self, schema: Mapping = None, tree: ErrorTree = None):
        """

        Args:
            schema (optional): Validation schema as dict[field, rule objects].
            tree (optional): Validation errors tree.
        """

        super().__init__()
        self.__set_custom_error_codes()
        self._custom_schema = schema

    def __set_custom_error_codes(self):
        """Add custom error codes specific to NACC validation rules."""
        # IMPORTANT - When adding a new error DON'T change the existing codes
        # Cerberus uses bit 5 and bit 7 to mark specific error types
        # Check https://docs.python-cerberus.org/customize.html for more info
        # Error messages are synced with ErrorDefs using the error code
        # Error codes are used to map b/w cerberus errors and NACC QC check codes
        custom_errors = {
            0x1000:
            "cannot be greater than current date {0}",
            0x1001:
            "cannot be greater than current year {0}",
            0x1002:
            "max date/year comparison error - {0}",
            0x1003:
            "cannot be less than current date {0}",
            0x1004:
            "cannot be less than current year {0}",
            0x1005:
            "min date/year comparison error - {0}",
            0x1006:
            "cannot be empty",
            0x1007:
            "must be empty",
            0x1008:
            "{1} for if {2} then {3} - compatibility rule no: {0}",
            0x1009:
            "{1} for if {2} else {3} - compatibility rule no: {0}",
            0x2000:
            "{1} in current visit for if {2} in previous visit then {3} in current visit - temporal rule no: {0}",
            0x2001:
            "primary key variable {0} not set in current visit data",
            0x2002:
            "failed to retrieve the previous visit, cannot proceed with validation",
            0x2003:
            "error in formula evaluation - {0}",
            0x2004:
            "If GDS not attempted (nogds=1), total GDS score should be 88 " +
            "- GDS rule no: {0}",
            0x2005:
            "If GDS not attempted (nogds=1), there cannot be >=12 questions with "
            + "valid scores - GDS rule no: {0}",
            0x2006:
            "incorrect GDS score {1}, expected value {2} - GDS rule no: {0}",
            0x2007:
            "If GDS attempted (nogds=blank), at least 12 questions need to have "
            + "valid scores - GDS rule no: {0}",
            0x2008:
            "input value doesn't satisfy the condition {0}",
            0x2009:
            "failed to retrieve record for previous visit, cannot proceed with "
            + "validation {0}",
            0x3000:
            "Drug ID {0} is not a valid RXCUI",
            0x3001:
            "failed to convert value {0} to a date: {1}",
            0x3002:
            "input value {0} doesn't satisfy the condition: {1}",
            0x3003:
            "Error in comparing {0} to age at {1} ({2}): {3}",
            0x3004:
            "{1} in previous visit for if {2} in current visit then {3} in previous visit - temporal rule no: {0}",
        }

        self.messages.update(custom_errors)

    def _format_message(self, field: str, error: ValidationError):
        """Display custom error message. Use the 'meta' tag in the schema to
        specify a custom error message e.g. "meta": {"errmsg": "<custom
        message>"}

        Args:
            field: Variable name
            error: Error object generated by applying validation rules
        """

        if self._custom_schema and field in self._custom_schema:
            error_msg = (self._custom_schema[field].get(
                SchemaDefs.META, {}).get(SchemaDefs.ERRMSG, ""))
            if error_msg:
                return field + ": " + error_msg

        return super()._format_message(field, error)


class SchemaDefs:
    """Class to store schema attribute labels."""

    TYPE = "type"
    OP = "op"
    IF_OP = "if_op"
    THEN_OP = "then_op"
    ELSE_OP = "else_op"
    IF = "if"
    THEN = "then"
    ELSE = "else"
    META = "meta"
    ERRMSG = "errmsg"
    ORDERBY = "orderby"
    CONSTRAINTS = "constraints"
    PREV_OP = "prev_op"
    CURR_OP = "curr_op"
    CURRENT = "current"
    PREVIOUS = "previous"
    CRR_DATE = "current_date"
    CRR_YEAR = "current_year"
    CRR_MONTH = "current_month"
    CRR_DAY = "current_day"
    PREV_RECORD = "previous_record"
    FORMULA = "formula"
    INDEX = "index"
    FORMATTING = "formatting"
    COMPARATOR = "comparator"
    BASE = "base"
    ADJUST = "adjustment"
    IGNORE_EMPTY = "ignore_empty"
    BIRTH_MONTH = 'birth_month'
    BIRTH_DAY = 'birth_day'
    BIRTH_YEAR = 'birth_year'
    COMPARE_TO = "compare_to"
    SWAP_ORDER = "swap_order"
