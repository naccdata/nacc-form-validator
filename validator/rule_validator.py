""" Module for defining validation rules """
import inspect
import logging

from datetime import datetime as dt
from typing import Mapping

from cerberus.errors import BasicErrorHandler, ValidationError, ErrorTree
from cerberus.validator import Validator

from validator.datastore import Datastore
from validator.json_logic import jsonLogic


class SchemaDefs:
    """ Class to store schema attribute labels and default values """

    TYPE = 'type'
    OP = 'op'
    IF = 'if'
    THEN = 'then'
    ELSE = 'else'
    META = 'meta'
    ERRMSG = 'errmsg'
    ORDERBY = 'orderby'
    CONSTRAINTS = 'constraints'
    CURRENT = 'current'
    PREVIOUS = 'previous'
    CRR_DATE = 'current_date'
    CRR_YEAR = 'current_year'
    FORMULA = 'formula'


class ValidationException(Exception):
    """ Raised when an system error occurs during validation """

    pass


class CustomErrorHandler(BasicErrorHandler):
    """ Class to provide custom error messages  """

    def __init__(self, schema: Mapping = None, tree: ErrorTree = None):
        """

        Args:
            schema (Mapping, optional): Validation schema as dict[field, rule objects].
            tree (ErrorTree, optional): Validation errors tree.
        """

        super().__init__()
        self._custom_schema = schema

    def _format_message(self, field: str, error: ValidationError):
        """ Display custom error message.
            Use the 'meta' tag in the schema to specify a custom error message
            e.g. "meta": {"errmsg": "<custom message>"}

        Args:
            field (str): Variable name
            error (ValidationError): Error object generated by applying validation rules

        """

        if self._custom_schema:
            error_msg = self._custom_schema[field].get(
                SchemaDefs.META, {}).get(SchemaDefs.ERRMSG, '')
            if error_msg:
                return field + ': ' + error_msg

        return super()._format_message(field, error)


class RuleValidator(Validator):
    """ RuleValidator class to extend cerberus.Validator """

    def __init__(self, schema: Mapping, *args, **kwargs):
        """

        Args:
            schema (Mapping): Validation schema as dict[field, rule objects]
        """

        super().__init__(schema, *args, **kwargs)

        # Data type map for each field
        self.__dtypes: dict[str, str] = self.__populate_data_types()

        # Datastore instance, will be set later for longitudinal projects
        # Not passing this as an attribute to init method as it causes errors inside cerberus code
        self.__datastore: Datastore = None

        # Primary key field of the project, will be set later for longitudinal projects
        # Not passing this as an attribute to init method as it causes errors inside cerberus code
        self.__pk_field: str = None

        # Cache of previous records that has been retrieved
        self.__prev_records: dict[str, Mapping] = {}

    @property
    def dtypes(self):
        """ The dtype property """
        return self.__dtypes

    def __populate_data_types(self) -> dict[str, str] | None:
        """ Convert cerberus data types to python data types.
            Populates a field->data type mapping for each field in the schema

        Returns:
            dict[str, str] : dict of [field, data_type]
            None: If no validation schema available
        """

        if not self.schema:
            return None

        data_types = {}
        for key, configs in self.schema.items():
            if SchemaDefs.TYPE in configs:
                if configs[SchemaDefs.TYPE] == 'integer':
                    data_types[key] = 'int'
                elif configs[SchemaDefs.TYPE] == 'string':
                    data_types[key] = 'str'
                elif configs[SchemaDefs.TYPE] == 'float':
                    data_types[key] = 'float'
                elif configs[SchemaDefs.TYPE] == 'boolean':
                    data_types[key] = 'bool'
                elif configs[SchemaDefs.TYPE] == 'date':
                    data_types[key] = 'date'
                elif configs[SchemaDefs.TYPE] == 'datetime':
                    data_types[key] = 'datetime'

        return data_types

    def set_datastore(self, datastore: Datastore):
        """ Set the Datastore instance

        Args:
            datastore (Datastore): Datastore instance to retrieve longitudinal data
        """

        self.__datastore: Datastore = datastore

    def set_primary_key_field(self, pk_field: str):
        """ Set the pk_field attribute

        Args:
            pk_field (str): Primary key field of the project
        """

        self.__pk_field: str = pk_field

    def reset_record_cache(self):
        """ Clear the previous records cache """

        self.__prev_records.clear()

    def cast_record(self, record: dict[str, str]) -> dict[str, object]:
        """ Cast the fields in the record to appropriate data types.

        Args:
            record (dict[str, str]): Input record dict[field, value]

        Returns:
            dict[str, object]: Casted record dict[field, value]
        """

        if not self.__dtypes:
            return record

        for key, value in record.items():
            # Set empty fields to None (to trigger nullable validations),
            # otherwise data type validation is triggered.
            # Don't remove empty fields from the record, if removed, any
            # validation rules defined for that field will not be triggered.
            if value == '':
                record[key] = None
                continue

            try:
                if key in self.__dtypes:
                    if self.__dtypes[key] == 'int':
                        record[key] = int(value)
                    elif self.__dtypes[key] == 'float':
                        record[key] = float(value)
                    elif self.__dtypes[key] == 'bool':
                        record[key] = bool(value)
                    elif self.__dtypes[key] == 'date':
                        record[key] = dt.strptime(value, '%Y-%m-%d').date()
                    elif self.__dtypes[key] == 'datetime':
                        record[key] = dt.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                logging.error('Failed to cast value %s to type %s - %s', value,
                              self.__dtypes[key], e)
                record[key] = value

        return record

    def _validate_max(self, max_value: object, field: str, value: object):
        """ Override max rule to support validations wrt current date/year

        Args:
            max_value (object): Maximum value specified in the schema def
            field (str): Variable name
            value (object): Variable value

            Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
            The rule's arguments are validated against this schema:
                {'nullable': False}
        """

        if max_value == SchemaDefs.CRR_DATE:
            dtype = self.__dtypes[field]
            curr_date = dt.now()
            if dtype == 'date':
                curr_date = curr_date.date()

            try:
                if value > curr_date:
                    self._error(field, 'cannot be greater than current date')
            except TypeError as e:
                self._error(field, str(e))
        elif max_value == SchemaDefs.CRR_YEAR:
            dtype = self.__dtypes[field]
            curr_date = dt.now()
            try:
                if value.year > curr_date.year:
                    self._error(field, 'cannot be greater than current year')
            except (TypeError, AttributeError) as e:
                self._error(field, str(e))
        else:
            super()._validate_max(max_value, field, value)

    def _validate_min(self, min_value: object, field: str, value: object):
        """ Override min rule to support validations wrt current date/year

        Args:
            min_value (object): Minimum value specified in the schema def
            field (str): Variable name
            value (object): Variable value

            Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
            The rule's arguments are validated against this schema:
                {'nullable': False}
        """

        if min_value == SchemaDefs.CRR_DATE:
            dtype = self.__dtypes[field]
            curr_date = dt.now()
            if dtype == 'date':
                curr_date = curr_date.date()

            try:
                if value < curr_date:
                    self._error(field, 'cannot be less than current date')
            except TypeError as e:
                self._error(field, str(e))
        elif min_value == SchemaDefs.CRR_YEAR:
            dtype = self.__dtypes[field]
            curr_date = dt.now()
            try:
                if value.year < curr_date.year:
                    self._error(field, 'cannot be less than current year')
            except (TypeError, AttributeError) as e:
                self._error(field, str(e))
        else:
            super()._validate_min(min_value, field, value)

    def _validate_filled(self, filled: bool, field: str, value: object):
        """ Custom method to check whether the 'filled' rule is met.
            This is different from 'nullable' rule.

        Args:
            filled (bool): Constraint value specified in the schema def
            field (str): Variable name
            value (object): Variable value

            Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
            The rule's arguments are validated against this schema:
                {'type': 'boolean'}
        """

        if not filled and value is not None:
            self._error(field, 'must be empty')
        elif filled and value is None:
            self._error(field, 'cannot be empty')

    def _validate_compatibility(self, constraints: list[Mapping], field: str,
                                value: object):
        """ Validate the list of compatibility checks specified for a field.

        Args:
            constraints (list[Mapping]): List of constraints specified for the variable
            field (str): Variable name
            value (object): Variable value

        Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
            The rule's arguments are validated against this schema:
                {'type': 'list',
                 'schema': {'type': 'dict',
                            'schema':{'op': {'type': 'string', 'required': False, 'allowed': ['AND', 'OR']},
                                      'if': {'type': 'dict', 'required': True, 'empty': False},
                                      'then': {'type': 'dict', 'required': True, 'empty': False},
                                      'else': {'type': 'dict', 'required': False, 'empty': False},
                                      'errmsg': {'type': 'string', 'required': False, 'empty': False}
                                      }
                            }
                }
        """

        # Evaluate each constraint in the list individually,
        # validation fails if any of the constraints fails.
        for constraint in constraints:
            # Extract operator if specified, default is AND
            operator = constraint.get(SchemaDefs.OP, 'AND')

            # Extract conditions for if clause
            dependent_conds = constraint[SchemaDefs.IF]

            # Extract conditions for then clause
            then_conds = constraint[SchemaDefs.THEN]

            # Extract conditions for else clause, this is optional
            else_conds = constraint.get(SchemaDefs.ELSE, None)

            # Extract error message if specified, this is optional
            err_msg = constraint.get(SchemaDefs.ERRMSG, None)

            valid = False
            # Check whether the dependency conditions satisfied
            for dep_field, conds in dependent_conds.items():
                subschema = {dep_field: conds}
                temp_validator = RuleValidator(
                    subschema,
                    allow_unknown=True,
                    error_handler=CustomErrorHandler(subschema))
                if operator == 'OR':
                    valid = valid or temp_validator.validate(self.document)
                # Evaluate as logical AND operation
                elif not temp_validator.validate(self.document):
                    valid = False
                    break

            subschema = None
            # If dependencies satisfied validate Then clause
            if valid:
                subschema = {field: then_conds}
            elif else_conds:  # If dependencies not satisfied validate Else clause, if there's any
                subschema = {field: else_conds}

            if subschema:
                temp_validator = RuleValidator(
                    subschema,
                    allow_unknown=True,
                    error_handler=CustomErrorHandler(subschema))
                if not temp_validator.validate(self.document):
                    if err_msg:
                        self._error(field, err_msg)
                    else:
                        errors = temp_validator.errors.items()
                        for error in errors:
                            self._error(field,
                                        f'{str(error)} for {dependent_conds}')

    def _validate_temporalrules(self, temporalrules: dict[Mapping], field: str,
                                value: object):
        """ Validate the list of longitudial checks specified for a field.

        Args:
            temporalrules (dict[Mapping]): Longitudial checks definitions for the variable
            field (str): Variable name
            value (object): Variable value

        Raises:
            ValidationException: If DataHandler or primary key not set

        Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
        The rule's arguments are validated against this schema:
            {'type': 'dict',
             'schema': {'orderby': {'type': 'string', 'required': True, 'empty': False},
                        'constraints': {'type': 'list',
                                        'schema': {'type': 'dict',
                                                    'schema': {'previous': {'type': 'dict', 'required': True, 'empty': False},
                                                                'current': {'type': 'dict', 'required': True, 'empty': False}
                                                            }
                                                }
                                        }
                        }
            }
        """
        if not self.__datastore:
            raise ValidationException(
                'Datastore not set, use set_datastore() method')

        if not self.__pk_field:
            raise ValidationException(
                'Primary key field not set, use set_primary_key_field() method'
            )

        record_id = self.document[self.__pk_field]

        # If the previous record was already retrieved, use it
        if record_id in self.__prev_records:
            prev_ins = self.__prev_records[record_id]
        else:
            orderby = temporalrules[SchemaDefs.ORDERBY]
            prev_ins = self.__datastore.get_previous_instance(
                orderby, self.document)

            if prev_ins:
                prev_ins = self.cast_record(prev_ins)

            self.__prev_records[record_id] = prev_ins

        if prev_ins:
            constraints = temporalrules[SchemaDefs.CONSTRAINTS]
            for constraint in constraints:
                prev_conds = constraint[SchemaDefs.PREVIOUS]
                prev_schema = {field: prev_conds}
                curr_conds = constraint[SchemaDefs.CURRENT]
                curr_schema = {field: curr_conds}
                err_msg = constraint.get(SchemaDefs.ERRMSG, None)

                prev_validator = RuleValidator(
                    prev_schema,
                    allow_unknown=True,
                    error_handler=CustomErrorHandler(prev_schema))
                if prev_validator.validate(prev_ins):
                    temp_validator = RuleValidator(
                        curr_schema,
                        allow_unknown=True,
                        error_handler=CustomErrorHandler(curr_schema))
                    if not temp_validator.validate({field: value}):
                        if err_msg:
                            self._error(field, err_msg)
                        else:
                            errors = temp_validator.errors.items()
                            for error in errors:
                                self._error(
                                    field,
                                    f'{str(error)} in current visit for {prev_conds} in previous visit'
                                )

    def _validate_logic(self, logic: dict[Mapping], field: str, value: object):
        """ Validate a mathematical formula/expression.

        Args:
            logic (dict[Mapping]): Validation logic specified in the rule definition
            field (str): Variable name
            value (object): Variable value

        Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
        The rule's arguments are validated against this schema:
            {'type': 'dict',
             'schema': {'formula': {'type': 'dict', 'required': True, 'empty': False},
                        'errmsg': {'type': 'string', 'required': False, 'empty': False}
                       }
            }

        """

        formula = logic[SchemaDefs.FORMULA]
        err_msg = logic.get(SchemaDefs.ERRMSG, None)
        if not err_msg:
            err_msg = f'Formula {formula} not satisfied'
        if not jsonLogic(formula, self.document):
            self._error(field, err_msg)

    def _validate_function(self, function: str, field: str,
                           value: object):
        """ Validate using a custom defined function

        Args:
            function (str): Function name
            field (str): Variable name
            value (object): Variable value

            Note: Don't remove below docstring, Cerberus uses it to validate the schema definition.
            The rule's arguments are validated against this schema:
                {'type': 'string', 'empty': False}
        """

        func = getattr(self, function, None)
        if func and callable(func):
            func(value)
        else:
            err_msg = f'{function} not defined in the validator module'
            self._error(field, err_msg)
            raise ValidationException(err_msg)

    def _check_with_gds(self, field: str, value: object):
        """ Validate Geriatric Depression Scale (GDS) calculation

        Args:
            field (str): Variable name
            value (object): Variable value
        """

        nogds = 0
        if 'nogds' in self.document:
            nogds = self.document['nogds']

        if nogds == 1 and value != 88:
            self._error(
                field, 'If GDS not attempted (nogds=1), total GDS score should be 88')
            return

        keys = ["satis", "dropact", "empty", "bored", "spirits", "afraid", "happy", "helpless",
                "stayhome", "memprob", "wondrful", "wrthless", "energy", "hopeless", "better"]

        num_valid = 0
        gds = 0
        for key in keys:
            if key in self.document and self.document[key] in [1, 0]:
                num_valid += 1
                gds += self.document[key]

        if nogds == 1 and num_valid >= 12:
            self._error(
                field, 'If GDS not attempted (nogds=1), there cannot be >=12 questions with valid scores')
            return

        if nogds == 0 and num_valid < 12:
            self._error(
                field, 'Need >=12 questions with valid scores to compute the total GDS score')
            return

        if num_valid > 0 and num_valid < 15:
            gds = round(gds + (gds/num_valid)*(15-num_valid))

        if gds != value:
            self._error(
                field, f'Incorrect total GDS score, current value {value}, expected value {gds}')
