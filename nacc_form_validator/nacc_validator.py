"""Module for defining NACC specific data validation rules (extending cerberus
library)."""

import logging
from datetime import datetime as dt
from typing import Any, Dict, List, Mapping, Optional, Tuple

from cerberus.validator import Validator
from dateutil import parser

from nacc_form_validator import utils
from nacc_form_validator.datastore import Datastore
from nacc_form_validator.errors import (
    CustomErrorHandler,
    ErrorDefs,
    SchemaDefs,
)
from nacc_form_validator.json_logic import jsonLogic

log = logging.getLogger(__name__)


class ValidationException(Exception):
    """Raised when an system error occurs during validation."""


class NACCValidator(Validator):
    """NACCValidator class to extend cerberus.Validator."""

    def __init__(self, schema: Mapping, *args, **kwargs):
        """
        Args:
            schema: Validation schema as Dict[variable, rule objects]
        """

        super().__init__(schema=schema, *args, **kwargs)

        # Data type map for each field
        self.__dtypes: Dict[str, str] = self.__populate_data_types()

        # Datastore instance
        self.__datastore: Datastore = None

        # Primary key field of the project
        self.__pk_field: str = None

        # Cache of previous records that has been retrieved
        self.__prev_records: Dict[str, Mapping] = {}

        # List of system errors occured by field
        self.__sys_errors: Dict[str, List[str]] = {}

    @property
    def dtypes(self) -> Dict[str, str]:
        """Returns the field->datatype mapping for the fields defined in the
        validation schema."""
        return self.__dtypes

    def __populate_data_types(self) -> Optional[Dict[str, str]]:
        """Convert cerberus data types to python data types. Populates a
        field->data type mapping for each field in the schema.

        Returns:
            Dict[str, str]: Dict of [field, data_type] or None
        """

        if not self.schema:
            return None

        data_types = {}
        for key, configs in self.schema.items():
            if SchemaDefs.TYPE in configs:
                if configs[SchemaDefs.TYPE] == "integer":
                    data_types[key] = "int"
                elif configs[SchemaDefs.TYPE] == "string":
                    data_types[key] = "str"
                elif configs[SchemaDefs.TYPE] == "float":
                    data_types[key] = "float"
                elif configs[SchemaDefs.TYPE] == "boolean":
                    data_types[key] = "bool"
                elif configs[SchemaDefs.TYPE] == "date":
                    data_types[key] = "date"
                elif configs[SchemaDefs.TYPE] == "datetime":
                    data_types[key] = "datetime"
                else:
                    log.warning(
                        "Unsupported datatype %s for field %s",
                        configs[SchemaDefs.TYPE],
                        key,
                    )

        return data_types

    @property
    def datastore(self) -> Optional[Datastore]:
        """Returns the datastore object or None."""
        return self.__datastore

    @datastore.setter
    def datastore(self, datastore: Datastore):
        """Set the Datastore instance.

        Args:
            datastore: Datastore instance to retrieve longitudinal data
        """

        self.__datastore = datastore

    @property
    def primary_key(self) -> Optional[str]:
        """Returns the primary key field name or None."""
        return self.__pk_field

    @primary_key.setter
    def primary_key(self, pk_field: str):
        """Set the pk_field attribute.

        Args:
            pk_field: Primary key field of the project
        """

        self.__pk_field = pk_field

    @property
    def sys_errors(self) -> Dict[str, List[str]]:
        """Returns the list of system errors occurred during validation.

        This is different from the validation errors and can be empty.
        Examples: Datastore not set for temporal checks
                  Error in rule definition file
        """
        return self.__sys_errors

    def __add_system_error(self, field: str, err_msg: str):
        """Add system error message.

        Args:
            field: Variable name
            err_msg: Error message
        """
        if field in self.__sys_errors:
            self.__sys_errors[field].append(err_msg)
        else:
            self.__sys_errors[field] = [err_msg]

    def reset_sys_errors(self):
        """Clear the system errors."""

        self.__sys_errors.clear()

    def reset_record_cache(self):
        """Clear the previous records cache."""

        self.__prev_records.clear()

    def get_error_messages(self) -> Dict[int, str]:
        """Returns the list of error messages by error code.

        Check ~cerberus.errors.BasicErrorHandler for more info.

        Returns:
            Dict[int, str]: list of error messages
        """
        return self.error_handler.messages

    def cast_record(self, record: Dict[str, str]) -> Dict[str, object]:
        """Cast the fields in the record to appropriate data types.

        Args:
            record: Input record Dict[field, value]

        Returns:
            Dict[str, object]: Casted record Dict[field, value]
        """

        if not self.dtypes:
            return record

        for key, value in record.items():
            # Set empty fields to None (to trigger nullable validations),
            # otherwise data type validation is triggered.
            # Don't remove empty fields from the record, if removed, any
            # validation rules defined for that field will not be triggered.
            if value == "":
                record[key] = None
                continue
            if value is None:
                continue

            if key in self.dtypes:
                try:
                    if self.dtypes[key] == "int":
                        record[key] = int(value)
                    elif self.dtypes[key] == "float":
                        record[key] = float(value)
                    elif self.dtypes[key] == "bool":
                        record[key] = bool(value)
                    elif self.dtypes[key] == "date":
                        record[key] = utils.convert_to_date(value)
                    elif self.dtypes[key] == "datetime":
                        record[key] = utils.convert_to_datetime(value)
                except (ValueError, TypeError, parser.ParserError) as error:
                    log.error(
                        "Failed to cast variable %s, value %s to type %s - %s",
                        key,
                        value,
                        self.dtypes[key],
                        error,
                    )
                    record[key] = value

        for key in self.schema:
            if key not in record:
                record[key] = None

        return record

    def __get_value_for_key(self, key: str) -> Optional[Any]:
        """Find the value for the specified key.

        Args:
            key: key (field name or special key such as current_year)

        Returns:
            Any: Value of the specified key or None
        """
        if key == SchemaDefs.CRR_DATE:
            return dt.now().date()

        if key == SchemaDefs.CRR_YEAR:
            return dt.now().date().year

        if key == SchemaDefs.CRR_MONTH:
            return dt.now().date().month

        if key == SchemaDefs.CRR_DAY:
            return dt.now().date().day

        if self.document and key in self.document:
            return self.document[key]

        # doesn't particularly matter if its an int or float in this case,
        # so just try cast to float
        try:
            key = float(key)
            return key
        except ValueError:
            pass

        return None

    # pylint: disable=(unused-argument)
    def _validate_formatting(self, formatting: str, field: str, value: object):
        """Adding formatting attribute to support specifying string dates. This
        is not an actual validation, just a placeholder method.

        Args:
            formatting: format specified in the schema def
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {
                'nullable': False,
                'type': 'string',
                'allowed': ['date', 'datetime']
            }
        """

        if field not in self.dtypes or self.dtypes[field] != "str":
            err_msg = "formatting definition not supported for non string types"
            self.__add_system_error(field, err_msg)
            raise ValidationException(err_msg)

    def _validate_max(self, max_value: object, field: str, value: object):
        """Override max rule to support validations wrt current date/year.

        Args:
            max_value: Maximum value specified in the schema def
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {'nullable': False}
        """

        if max_value in (SchemaDefs.CRR_DATE, SchemaDefs.CRR_YEAR):
            dtype = self.dtypes[field] if field in self.dtypes else "undefined"
            try:
                if dtype == "str":
                    input_date = utils.convert_to_date(value)
                elif dtype == "date":
                    input_date = value
                elif dtype == "datetime":
                    input_date = value.date()
                elif dtype == "int" and max_value == SchemaDefs.CRR_YEAR:
                    input_date = dt(value, 1, 1).date()
                else:
                    message = f"{max_value} not supported for {dtype} datatype"
                    self._error(field, ErrorDefs.INVALID_DATE_MAX, message)
                    return
            except (ValueError, TypeError, parser.ParserError) as error:
                self._error(field, ErrorDefs.INVALID_DATE_MAX, str(error))
                return

            curr_date = dt.now().date()

            if max_value == SchemaDefs.CRR_DATE and input_date > curr_date:
                self._error(field, ErrorDefs.CURR_DATE_MAX, str(curr_date))
            elif max_value == SchemaDefs.CRR_YEAR and input_date.year > curr_date.year:
                self._error(field, ErrorDefs.CURR_YEAR_MAX, curr_date.year)
        else:
            if SchemaDefs.FORMATTING in self.schema[field]:
                methodname = f"convert_to_{self.schema[field][SchemaDefs.FORMATTING]}"
                func = getattr(utils, methodname, None)
                if func and callable(func):
                    try:
                        max_value = func(max_value)
                        value = func(value)
                    except (
                            AttributeError,
                            parser.ParserError,
                            TypeError,
                            ValueError,
                    ) as error:
                        self._error(field, ErrorDefs.INVALID_DATE_MAX,
                                    str(error))
                        return
                else:
                    err_msg = f"{methodname} not defined in the validator module"
                    self.__add_system_error(field, err_msg)
                    raise ValidationException(err_msg)

            super()._validate_max(max_value, field, value)

    def _validate_min(self, min_value: object, field: str, value: object):
        """Override min rule to support validations wrt current date/year.

        Args:
            min_value: Minimum value specified in the schema def
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {'nullable': False}
        """

        if min_value in (SchemaDefs.CRR_DATE, SchemaDefs.CRR_YEAR):
            dtype = self.dtypes[field] if field in self.dtypes else "undefined"
            try:
                if dtype == "str":
                    input_date = utils.convert_to_date(value)
                elif dtype == "date":
                    input_date = value
                elif dtype == "datetime":
                    input_date = value.date()
                elif dtype == "int" and min_value == SchemaDefs.CRR_YEAR:
                    input_date = dt(value, 1, 1).date()
                else:
                    message = f"{min_value} not supported for {dtype} datatype"
                    self._error(field, ErrorDefs.INVALID_DATE_MIN, message)
                    return
            except (ValueError, TypeError, parser.ParserError) as error:
                self._error(field, ErrorDefs.INVALID_DATE_MIN, str(error))
                return

            curr_date = dt.now().date()

            if min_value == SchemaDefs.CRR_DATE and input_date < curr_date:
                self._error(field, ErrorDefs.CURR_DATE_MIN, str(curr_date))
            elif min_value == SchemaDefs.CRR_YEAR and input_date.year < curr_date.year:
                self._error(field, ErrorDefs.CURR_YEAR_MIN, curr_date.year)
        else:
            if SchemaDefs.FORMATTING in self.schema[field]:
                methodname = f"convert_to_{self.schema[field][SchemaDefs.FORMATTING]}"
                func = getattr(utils, methodname, None)
                if func and callable(func):
                    try:
                        min_value = func(min_value)
                        value = func(value)
                    except (
                            AttributeError,
                            parser.ParserError,
                            TypeError,
                            ValueError,
                    ) as error:
                        self._error(field, ErrorDefs.INVALID_DATE_MIN,
                                    str(error))
                        return
                else:
                    err_msg = f"{methodname} not defined in the validator module"
                    self.__add_system_error(field, err_msg)
                    raise ValidationException(err_msg)

            super()._validate_min(min_value, field, value)

    def _validate_filled(self, filled: bool, field: str, value: object):
        """Custom method to check whether the 'filled' rule is met. This is
        different from 'nullable' rule.

        Args:
            filled: Constraint value specified in the schema def
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {'type': 'boolean'}
        """

        if not filled and value is not None:
            self._error(field, ErrorDefs.FILLED_FALSE)
        elif filled and value is None:
            self._error(field, ErrorDefs.FILLED_TRUE)

    def _check_subschema_valid(self, all_conditions: Dict[str, object],
                               operator: str) -> Tuple[bool, object]:
        """Creates a temporary validator to check a set of conditions.

        Args:
            all_conditions: Set of conditions to be validated
            operator: Logical operation (AND | OR) to merge the conditions

        Returns:
            Tuple[bool, object]: Validation result, errors
        """
        valid = operator != "OR"
        errors = {}

        for field, conds in all_conditions.items():
            subschema = {field: conds}

            temp_validator = NACCValidator(
                subschema,
                allow_unknown=True,
                error_handler=CustomErrorHandler(subschema),
            )
            if operator == "OR":
                valid = valid or temp_validator.validate(self.document,
                                                         normalize=False)
                # if something passed, don't need to evaluate rest,
                # and ignore any errors found
                if valid:
                    errors = None
                    break
                # otherwise keep track of all errors
                errors.update(temp_validator.errors)

            # Evaluate as logical AND operation
            elif not temp_validator.validate(self.document, normalize=False):
                valid = False
                errors = temp_validator.errors
                break

        return valid, errors

    # pylint: disable=(too-many-locals, unused-argument)
    def _validate_compatibility(self, constraints: List[Mapping], field: str,
                                value: object):
        """Validate the List of compatibility checks specified for a field.

        Args:
            constraints: List of constraints specified for the variable
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'index': {'type': 'integer', 'required': False},
                        'if_op': {'type': 'string', 'required': False, 'allowed': ['AND', 'OR', 'and', 'or']},
                        'then_op': {'type': 'string', 'required': False, 'allowed': ['AND', 'OR', 'and', 'or']},
                        'else_op': {'type': 'string', 'required': False, 'allowed': ['AND', 'OR', 'and', 'or']},
                        'if': {'type': 'dict', 'required': True, 'empty': False},
                        'then': {'type': 'dict', 'required': True, 'empty': False},
                        'else': {'type': 'dict', 'required': False, 'empty': False}
                    }
                }
            }
        """

        # Evaluate each constraint in the List individually,
        # validation fails if any of the constraints fails.
        rule_no = -1
        for constraint in constraints:
            # Extract operators if specified, default is AND
            if_operator = constraint.get(SchemaDefs.IF_OP, "AND").upper()
            then_operator = constraint.get(SchemaDefs.THEN_OP, "AND").upper()
            else_operator = constraint.get(SchemaDefs.ELSE_OP, "AND").upper()

            # Extract constraint index if specified, or increment by 1
            rule_no = constraint.get(SchemaDefs.INDEX, rule_no + 1)

            # Extract conditions for if clause
            if_conds = constraint[SchemaDefs.IF]

            # Extract conditions for then clause
            then_conds = constraint[SchemaDefs.THEN]

            # Extract conditions for else clause, this is optional
            else_conds = constraint.get(SchemaDefs.ELSE, None)

            # Check if dependencies satisfied the If clause
            error_def = ErrorDefs.COMPATIBILITY_FALSE
            errors = None
            valid, _ = self._check_subschema_valid(if_conds, if_operator)

            # If the If clause valid, validate the Then clause
            if valid:
                valid, errors = self._check_subschema_valid(
                    then_conds, then_operator)
                error_def = ErrorDefs.COMPATIBILITY_TRUE

            # Otherwise validate the else clause, if they exist
            elif else_conds:
                valid, errors = self._check_subschema_valid(
                    else_conds, else_operator)
                error_def = ErrorDefs.COMPATIBILITY_FALSE
            else:  # if the If condition is not satisfied, do nothing
                pass

            # Something in the then/else clause failed - report errors
            if errors:
                for error in errors.items():
                    self._error(field, error_def, rule_no, str(error),
                                if_conds)

    # pylint: disable=(too-many-locals)
    def _validate_temporalrules(self, temporalrules: List[Mapping], field: str,
                                value: object):
        """Validate the List of longitudial checks specified for a field.

        Args:
            temporalrules: Longitudial checks definitions for the variable
            field: Variable name
            value: Variable value

        Raises:
            ValidationException: If Datastore or primary key not set

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'index': {'type': 'integer', 'required': False},
                        'prev_op': {'type': 'string', 'required': False, 'allowed': ['AND', 'OR', 'and', 'or']},
                        'curr_op': {'type': 'string', 'required': False, 'allowed': ['AND', 'OR', 'and', 'or']},
                        'previous': {'type': 'dict', 'required': True, 'empty': False},
                        'current': {'type': 'dict', 'required': True, 'empty': False}
                    }
                }
            }
        """

        if not self.datastore:
            err_msg = "Datastore not set, cannot validate temporal rules"
            self.__add_system_error(field, err_msg)
            raise ValidationException(err_msg)

        if not self.primary_key:
            err_msg = "Primary key field not set, cannot validate temporal rules"
            self.__add_system_error(field, err_msg)
            raise ValidationException(err_msg)

        if self.primary_key not in self.document or not self.document[
                self.primary_key]:
            self._error(field, ErrorDefs.NO_PRIMARY_KEY, self.primary_key)
            return

        record_id = self.document[self.primary_key]

        # If the previous record was already retrieved, use it
        if record_id in self.__prev_records:
            prev_ins = self.__prev_records[record_id]
        else:
            prev_ins = self.__datastore.get_previous_record(self.document)

            if prev_ins:
                prev_ins = self.cast_record(prev_ins)

            self.__prev_records[record_id] = prev_ins

        # If temporal rules are defined, a previous vist must exist
        if prev_ins is None:
            self._error(field, ErrorDefs.NO_PREV_VISIT)
            return

        rule_no = -1
        for temporalrule in temporalrules:
            # Extract operators if specified, default is AND
            prev_operator = temporalrule.get(SchemaDefs.PREV_OP, "AND").upper()
            curr_operator = temporalrule.get(SchemaDefs.CURR_OP, "AND").upper()

            rule_no = temporalrule.get(SchemaDefs.INDEX, rule_no + 1)
            prev_conds = temporalrule[SchemaDefs.PREVIOUS]
            curr_conds = temporalrule[SchemaDefs.CURRENT]

            errors = None
            # Check if conditions for the previous visit is satisfied
            valid, _ = self._check_subschema_valid(prev_conds, prev_operator)

            # If not satisfied, continue to next rule
            if not valid:
                continue

            # If satisfied, validate the current visit
            valid, errors = self._check_subschema_valid(
                curr_conds, curr_operator)

            # Cross visit validation failed - report errors
            if not valid and errors:
                for error in errors.items():
                    self._error(field, ErrorDefs.TEMPORAL, rule_no, str(error),
                                prev_conds)

    def _validate_logic(self, logic: Dict[str, Any], field: str,
                        value: object):
        """Validate a mathematical formula/expression.

        Args:
            logic: Validation logic specified in the rule definition
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {
                'type': 'dict',
                'schema': {
                    'formula': {'type': 'dict', 'required': True, 'empty': False},
                    'errmsg': {'type': 'string', 'required': False, 'empty': False}
                }
            }
        """

        formula = logic[SchemaDefs.FORMULA]
        err_msg = logic.get(SchemaDefs.ERRMSG, None)
        if not err_msg:
            err_msg = f"value {value} does not satisfy the specified formula"
        try:
            if not jsonLogic(formula, self.document):
                self._error(field, ErrorDefs.FORMULA, err_msg)
        except ValueError as error:
            self._error(field, ErrorDefs.FORMULA, str(error))

    def _validate_function(self, function: str, field: str, value: object):
        """Validate using a custom defined function.

        Args:
            function: Function name
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {'type': 'string', 'empty': False}
        """

        func = getattr(self, function, None)
        if func and callable(func):
            func(value)
        else:
            err_msg = f"{function} not defined in the validator module"
            self.__add_system_error(field, err_msg)
            raise ValidationException(err_msg)

    def _validate_compute_gds(self, keys: List[str], field: str,
                              value: object):
        """Validate Geriatric Depression Scale (GDS) calculation.

        Args:
            keys: GDS computation fields specified in the rule definition
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {
                'type': 'list',
                'minlength': 15,
                'schema': {'type': 'string'}
            }
        """

        nogds = 0
        if "nogds" in self.document:
            nogds = self.document["nogds"]

        num_valid = 0
        gds = 0
        for key in keys:
            if key in self.document and self.document[key] in [1, 0]:
                num_valid += 1
                gds += self.document[key]

        if nogds == 1:
            if value != 88:
                self._error(field, ErrorDefs.CHECK_GDS_1, 0)

            if num_valid >= 12:
                self._error(field, ErrorDefs.CHECK_GDS_2, 1)

            return

        if num_valid == 15 and gds != value:
            self._error(field, ErrorDefs.CHECK_GDS_3, 2, value, gds)
            return

        if (15 - num_valid) <= 3:
            gds = round(gds + (gds / num_valid) * (15 - num_valid))
            if gds != value:
                self._error(field, ErrorDefs.CHECK_GDS_4, 3, value, gds)

        if not nogds and num_valid < 12:
            self._error(field, ErrorDefs.CHECK_GDS_5, 4)
            return

    def _validate_compare_with(self, comparison: Dict[str, Any], field: str,
                               value: object):
        """Apply the specified comparison.

        Args:
            comparison: Comparison specified in the rule definition
            field: Variable name
            value: Variable value

        Note: Don't remove below docstring,
        Cerberus uses it to validate the schema definition.

        The rule's arguments are validated against this schema:
            {
                'type': 'dict',
                'schema': {
                    'comparator': {
                        'type': 'string',
                        'required': True,
                        'empty': False,
                        'allowed': [">", "<", ">=", "<=", "==", "!="]
                    },
                    'base': {
                        'type': ['string', 'number'],
                        'required': True,
                        'empty': False
                    },
                    'adjustment': {
                        'type': ['string', 'number'],
                        'required': False,
                        'empty': False,
                        'dependencies': 'op'
                    },
                    'op': {
                        'type': 'string',
                        'required': False,
                        'empty': False,
                        'allowed': ["+", "-", "*", "/"],
                        'dependencies': 'adjustment'
                    }
                }
            }
        """

        comparator = comparison[SchemaDefs.COMPARATOR]
        base = comparison[SchemaDefs.BASE]
        adjustment = None
        operator = None
        if SchemaDefs.ADJUST in comparison:
            adjustment = comparison[SchemaDefs.ADJUST]
        if SchemaDefs.OP in comparison:
            operator = comparison[SchemaDefs.OP]

        comparison_str = field + " " + comparator
        if adjustment and operator:
            comparison_str += " " + base + " " + operator + " " + str(
                adjustment)

        base_val = self.__get_value_for_key(base) if isinstance(base,
                                                                str) else base

        if base_val is None:
            self._error(field, ErrorDefs.COMPARE_WITH, comparison_str)
            return

        adjusted_value = base_val
        if adjustment and operator:
            adjustment = (self.__get_value_for_key(adjustment) if isinstance(
                adjustment, str) else adjustment)
            if operator == "+":
                adjusted_value = base_val + adjustment
            elif operator == "-":
                adjusted_value = base_val - adjustment
            elif operator == "*":
                adjusted_value = base_val * adjustment
            elif operator == "/":
                adjusted_value = base_val / adjustment

        try:
            valid = True
            if comparator == ">=" and value < adjusted_value:
                valid = False

            if comparator == ">" and value <= adjusted_value:
                valid = False

            if comparator == "<=" and value > adjusted_value:
                valid = False

            if comparator == "<" and value >= adjusted_value:
                valid = False

            if comparator == "==" and value != adjusted_value:
                valid = False

            if comparator == "!=" and value == adjusted_value:
                valid = False

            if not valid:
                self._error(field, ErrorDefs.COMPARE_WITH, comparison_str)
        except TypeError:
            self._error(field, ErrorDefs.COMPARE_WITH, comparison_str)
