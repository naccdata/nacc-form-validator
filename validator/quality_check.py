""" Module for performing data quality checks """

import logging
from typing import Any, Dict, List, Mapping, Tuple

from cerberus.schema import SchemaError
from validator.datastore import Datastore
from validator.nacc_validator import (CustomErrorHandler, NACCValidator,
                                      ValidationException)

log = logging.getLogger(__name__)


class QualityCheckException(Exception):
    """ Raised if something goes wrong while loading rule definitions """


class QualityCheck:
    """ Class to initiate validator object with the provided schema
    and run the data quality checks """

    def __init__(self,
                 pk_field: str,
                 schema: Mapping,
                 strict: bool = True,
                 datastore: Datastore = None):
        """

        Args:
            pk_field: Primary key field of the project
            schema: Validation rules schema as Dict[field, rule objects].
            strict (optional): Validation mode, defaults to True.
                        If False, unknown forms/fields are skipped from validation.
            datastore (optional): Datastore instance to retrieve longitudinal data.
        """

        self.__pk_field: str = pk_field
        self.__strict = strict
        self.__schema: Dict[str, Mapping[str, object]] = schema

        # Validator object for rule evaluation
        self.__validator: NACCValidator = None
        self.__init_validator(datastore)

    @property
    def schema(self) -> Dict[str, Mapping[str, object]]:
        """ The schema property

        Returns:
            Dict[str, Mapping[str, object]]:
            Schema of validation rules defined in the project
        """
        return self.__schema

    @property
    def validator(self) -> NACCValidator:
        """ The validator property

        Returns:
            NACCValidator: Validator object for rule evaluation
        """
        return self.__validator

    def __init_validator(self, datastore: Datastore = None):
        """ Initialize the validator object

        Raises:
            QualityCheckException: If there is an schema error
        """
        try:
            self.__validator = NACCValidator(self.__schema,
                                             allow_unknown=not self.__strict,
                                             error_handler=CustomErrorHandler(
                                                 self.__schema))
            self.__validator.primary_key = self.__pk_field
            self.__validator.datastore = datastore
        except SchemaError as error:
            raise QualityCheckException(f'Schema Error - {error}') from error

    def validate_record(
        self, record: Dict[str, str]
    ) -> Tuple[bool, Dict[str, List[str]], Dict[str, Any]]:
        """ Evaluate the record against the defined rules using cerberus.

        Args:
            record (Dict[str, str]): Record to be validated, Dict[field, value]

        Returns:
            bool: True if the record satisfied all rules
            Dict[str, List[str]: List of formatted error messages by variable
            Dict[str, Any]: Dict of ValidationError objects by variable
        """

        # All the fields in the input record represented as string values,
        # cast the fields to appropriate data types according to the schema
        cst_record = self.__validator.cast_record(record.copy())

        # Validate the record against the defined schema
        sys_errors = False
        passed = False
        try:
            passed = self.__validator.validate(cst_record, normalize=False)
        except ValidationException:
            sys_errors = True

        if sys_errors:
            log.error('System error(s) occurred during validation, '
                      'please fix the issues below and retry '
                      'or contact the system administrator.')
            log.error(self.__validator.sys_erros)
            errors = self.__validator.sys_erros
            error_tree = None
        else:
            errors = self.__validator.errors
            error_tree = self.__validator.document_error_tree

        return passed, errors, error_tree
