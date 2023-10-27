""" Module for performing data quality checks """

import logging
import cerberus.schema

from typing import Mapping, Tuple

from validator.datastore import Datastore
from validator.parser import Parser
from validator.rule_validator import CustomErrorHandler, RuleValidator, ValidationException


class QualityCheckException(Exception):
    """ Raised if something goes wrong while loading rule definitions """

    pass


class QualityCheck:
    """ Class to load the rule definitions and run the quality checks """

    def __init__(self,
                 pk_field: str,
                 rules_dir: str,
                 rules_type: str,
                 forms: list[str],
                 strict: bool = True,
                 datastore: Datastore = None):
        """

        Args:
            pk_field (str): Primary key field of the project
            rules_dir (str): Location where rule definitions are stored
            rules_type (str): Rule definitions type - yaml or json
            forms (list[str]): List of form names to load the rule definitions
            strict (bool, optional): Validation mode. Defaults to True.
                                     If False, unknown forms/fields are skipped from validation
        """

        self.__pk_field: str = pk_field
        self.__strict = strict
        # Schema of validation rules defined in the project by variable name
        self.__schema: dict[str, Mapping[str, object]] = {}

        self.__load_rules(rules_dir, rules_type, forms)

        # Validator object for rule evaluation
        self.__validator: RuleValidator = self.__init_validator(datastore)

    @property
    def schema(self) -> dict[str, Mapping[str, object]]:
        """ The schema property

        Returns:
            dict[str, Mapping[str, object]]: Schema of validation rules defined in the project
        """
        return self.__schema

    @property
    def validator(self) -> RuleValidator:
        """ The validator property

        Returns:
            RuleValidator: Validator object for rule evaluation
        """
        return self.__validator

    def __load_rules(self, rules_dir: str, rules_type: str, forms: list[str]):
        """ Load the set of validation rules defined for the variables

        Args:
            rules_dir (str): Location where rule definitions are stored
            rules_type (str): Rule definitions type - yaml or json
            forms (list[str]): List of form names to load the rule definitions

        Raises:
            QualityCheckException: If there is an error loading the rule definitions for the specified forms
        """

        if forms:
            parser = Parser(rules_dir, rules_type)
            self.__schema, found_all = parser.load_validation_schema(forms)
            if not found_all:
                raise QualityCheckException(
                    f'Error in loading rule definitions, please check {rules_dir} directory'
                )
        else:
            logging.warning(
                'No forms are specified to load the rule definitions, skipping validation rules'
            )

    def __init_validator(self, datastore: Datastore = None):
        """ Initialize the validator object

        Raises:
            QualityCheckException: If there is an schema error
        """
        try:
            self.__validator = RuleValidator(self.__schema,
                                             allow_unknown=not self.__strict,
                                             error_handler=CustomErrorHandler(
                                                 self.__schema))
            self.__validator.set_primary_key_field(self.__pk_field)
            self.__validator.set_datastore(datastore)
        except cerberus.schema.SchemaError as e:
            raise QualityCheckException(f'Schema Error - {e}')

    def check_record_cerberus(
            self, record: dict[str, str]) -> Tuple[bool, dict[str, list[str]]]:
        """ Evaluate the record against the defined rules using cerberus.

        Args:
            record (dict[str, str]): Record to be validated, dict[field, value]

        Returns:
            bool: True if the record satisfied all rules
            dict[str, list[str]: List of validation errors by variable (if any)
        """

        # All the fields in the input record represented as string values,
        # cast the fields to appropriate data types according to the schema before validation
        cst_record = self.__validator.cast_record(record.copy())
        # Validate the record against the defined schema
        try:
            passed = self.__validator.validate(cst_record, normalize=False)
        except ValidationException as e:
            passed = False

        errors = self.__validator.errors

        return passed, errors
