# Using the NACC Form Validator

The purpose of this package is to provide developers with ways to validate and run error checks on NACC-specific forms before submission, or for validating extra data your forms may have.

See [Data Quality Rule Definition Guidelines](./data-quality-rule-definition-guidelines.md) for more information on how the quality rules themselves work, which includes custom rules written specifically for NACC forms.

## Table of Contents

- [Using the NACC Form Validator](#using-the-nacc-form-validator)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Example Usage - Hello World](#example-usage---hello-world)
  - [Example Usage - Records and Datastores](#example-usage---records-and-datastores)
  - [Example Usage - Bulk Validation](#example-usage---bulk-validation)
  - [NACC Published JSON Rule Definitions for Form Data Validation](#nacc-published-json-rule-definitions-for-form-data-validation)
  - [Mapping Validation Errors to Human-Readable Messages](#mapping-validation-errors-to-human-readable-messages)

## Overview

The NACC Form Validator primarily consists of two classes: `QualityCheck`, which in turn creates a `NACCValidator`. Together they are used to validate a record against a validation schema. The `NACCValidator` itself is an extension of [Cerberus' `Validator` class](https://docs.python-cerberus.org/api.html#cerberus.Validator), and provides definitions for custom NACC rules. These custom rules are described in more detail in [Data Quality Rule Definition Guidelines](./data-quality-rule-definition-guidelines.md).

The `NACCValidator` can also use an an optional `Datastore` object which you can implement to access records in your own database. See [Example Usage - Records and Datastores](#example-usage---records-and-datastores) for more information.

The usage workflow is to instantiate a `QualityCheck` object with the schema you want to validate against, and then pass the record to validate to the `validate_record` method. This method returns 4 variables:

| Variable      | Type                   | Description                                                                                                                                                 |
| ------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `passed`      | `bool`                 | Whether or not the record satisfied all validation rules defined by the schema                                                                              |
| `sys_failure` | `bool`                 | Whether or not a system error occured                                                                                                                       |
| `errors`      | `dict[str, list[str]]` | Dict of errors encountered keyed by the variable that failed. Empty if no errors encountered for the record.                                                |
| `error_tree`  | `DocumentErrorTree`    | A dict-like object of `ValidationError` instances. See [Cerberus' Errors documentation](https://docs.python-cerberus.org/errors.html) for more information. |

## Example Usage - Hello World

The following is a simple example of using this package. The schema contains rules for the field `hello`, which can only be assigned to the string `world`, and the primary key `example_primary_key`, which must be an integer. The primary key should always be a required field in the schema.

```python
from nacc_form_validator import QualityCheck

pk_name = "example_primary_key"

schema = {
    "example_primary_key": {
        "type": "integer"
        "required", True
    },
    "hello": {
        "type": "string",
        "required": True,
        "allowed": [
            "world"
        ]
    }
}

qc = QualityCheck(pk_name, schema, strict=True, datastore=None)

passed, sys_failure, errors, error_tree = qc.validate_record({"example_primary_key": 1, "hello": "world"})
# passed = True
# sys_failure = False
# errors = {}
# error_tree = [],{}

passed, sys_failure, errors, error_tree = qc.validate_record({"example_primary_key": 2, "hello": "pluto"})
# passed = False
# sys_failure = False
# errors = {'hello': ['unallowed value pluto']}
# error_tree = [],{
#     'hello': [
#         ValidationError @ 0x101649390 ( document_path=('hello',),
#                                         schema_path=('hello', 'allowed'),
#                                         code=0x44,
#                                         constraint=['world'],
#                                         value="pluto",
#                                         info=('pluto',)
#                                        )
#         ],
#         {}
#     }
```

## Example Usage - Records and Datastores

You may want to compare a record against previous records, particularly if your schema uses temporal rules, which are usually associated with plausibility checks. This is where `pk_name` and `datastore` come in, in which `pk_name` must be the "primary key" to index the datastore by. The primary key must always be a required field. `datastore.py` then provides a `Datastore` abstract class that you must implement, specifically the `get_previous_record` method. 

For more information on temporal rules, see [Data Quality Rule Definition Guidelines](./data-quality-rule-definition-guidelines.md) for more information on temporal rules). If you are validating against a schema that doesn't have temporal rules, it isn't really necessary to set up a datastore.

As an example, say `pk_name` is the `patient_id`. For sake of simplicity, the "database" in this example will be a hard-coded Python dict, but yours will likely be much more complicated. Next our validation scheme checks to see if a patient filled out taxes in a previous visit (0); if so, the current record cannot indicate that they never did it (8).

```python
import copy

from nacc_form_validator import QualityCheck
from nacc_form_validator.datastore import Datastore


class CustomDatastore(Datastore):

    def __init__(self, pk_field: str, orderby: str) -> None:
        self.__db = {
            'PatientID1': [
                {
                    "visit_num": 1,
                    "taxes": 8
                },
                {
                    "visit_num": 2,
                    "taxes": 0
                }
            ]
        }
        super.__init__(pk_field, orderby)

    def get_previous_record(self, current_record: dict[str, str]) -> dict[str, str] | None:
        """
        See where current record would fit in the sorted record and return the previous record
        Making a deep copy since we don't actually want to modify the record in this method
        """
        key = current_record[self.pk_field]
        if key not in self.__db:
            return None

        sorted_record = copy.deepcopy(self.__db[key])
        sorted_record.append(current_record)
        sorted_record.sort(key=lambda record: record[self.__orderby])

        index = sorted_record.index(current_record)
        return sorted_record[index - 1] if index != 0 else None


pk_name = "patient_id"
orderby = "visit_num"
datastore = CustomDatastore(pk_name, orderby)

schema = {
    "patient_id": {
        "type": "string",
        "required": True
    },
    "visit_num": {
        "type": "integer",
        "required": True
    },
     "taxes": {
        "type": "integer",
        "temporalrules": [            
            {
                "previous": {
                    "taxes": {
                        "allowed": [0]
                    }
                },
                "current": {
                    "taxes": {
                        "forbidden": [8]
                    }
                }
            }
        ]
    }
}

qc = QualityCheck(pk_name, schema, strict=True, datastore=datastore)

record = {
    "patient_id": "PatientID1",
    "visit_num": 3,
    "taxes": 1
}

passed, sys_failure, errors, error_tree = qc.validate_record(record)
# passed = True
# sys_failure = False
# errors = {}
# error_tree = [],{}

record = {
    "patient_id": "PatientID1",
    "visit_num": 3,
    "taxes": 8
}

passed, sys_failure, errors, error_tree = qc.validate_record(record)
# passed = False
# sys_failure = False
# errors = {
#     'taxes': [
#         "('taxes',['unallowed value 8']) in current visit for {'allowed': [0]} in previous visit - temporal rule no: 1"
#         ]
#     }
# error_tree = [],{
#     'taxes': [
#         ValidationError @ 0x100a70ed0 ( document_path=('taxes',),
#                                         schema_path=('taxes', 'temporalrules'),
#                                         code=0x2000,
#                                         constraint={
#                                                "previous": {
#                                                    "taxes": {
#                                                        "allowed": [0]
#                                                    }
#                                                },
#                                                "current": {
#                                                    "taxes": {
#                                                        "forbidden": [8]
#                                                    }
#                                                }
#                                          },
#                                         value=8,
#                                         info=(1, "('taxes', ['unallowed value 8'])",{'allowed': [0]})
#                                         )
#     ],{}
# }
```

## Example Usage - Bulk Validation

It is likely you will want to validate multiple records at once. This is easily achieved by instantiating a `QualityCheck` with the corresponding schema and looping over the record(s) you want to validate as Python `dict` objects. What this data looks like outside of that is up to you - maybe you wish to read in forms from external files (JSONs, YAML, or CSVs), or directly from a database.

`docs/validate_csv_records.py` sets up an example CLI script to read in multiple records from a CSV file (where each row is a record) and validate them against a schema passed as a JSON file. It then summarizes the results and prints them to a CSV or JSON file (based on file extension, defaults to CSV if no extension is provided), or `stdout` (in JSON) if no output file is specified.

Example usage:

```bash
python3 validate_csv_records.py \
    -r rules-schema.json \
    -i input-records.csv \
    -o output-errors.csv
```

## NACC Published JSON Rule Definitions for Form Data Validation

NACC-published data quality checks for each form data module can be downloaded in [CSV](https://docs.naccdata.org/edc/data-quality-processing/nacc-published-checks#data-quality-checks) and [JSON](https://docs.naccdata.org/edc/data-quality-processing/nacc-published-checks#json-rule-definitions) formats from NACC's [Electronic Data Capture Documentation](https://docs.naccdata.org/edc/data-quality-processing/nacc-published-checks) page.

JSON rule definitions for a module are distributed as a zip file, organized by version, packet, and form. Merge all the rule definition files under a given packet code to get the full validation schema for that module/version/packet. Optional forms have an additional rule definition file named `<formname>_rules_optional.json`; if an optional form is not submitted, use this file in place of the regular rule definition file when building the validation schema.

Each module/version/packet also has a `codes` directory containing an error code mapping schema for each form. These JSON files can be used to [map the validator generated errors to human-readable messages](#mapping-validation-errors-to-human-readable-messages). Similar to rule definitions, merge all the code mapping files under a given packet code to get the full error code mapping schema for that module/version/packet. If an optional form is not submitted, use the `<formname>_codes_optional.json` file.

## Mapping Validation Errors to Human-Readable Messages

The `errors` dict returned by `validate_record` already contains a generic message for each failed field, but you'll often want to show your own wording instead - sourced from wherever you maintain published error text (a database, a flat file, an internal API, and so on), and possibly keyed by a stable code rather than the validator's internal rule name. The `error_tree` return value gives you access to the raw `ValidationError` objects needed to do this: each one exposes `rule` (the schema rule that failed, e.g. `"max"` or `"compatibility"`), `value`, `constraint`, and `info` (extra context used to build the default message).

A simple approach is to keep two things separate from the schema itself:

- An **error code map**, assigning a stable, publishable code to each field/rule pair you care to override. This is kept apart from the schema because rule names like `"max"` are implementation details of the validator, not identifiers meant to be shown to end users.
- An **error message store**, which looks up message text for a given code. You implement this against whatever system publishes your error text, the same way you'd implement the `Datastore` abstract class (see [Example Usage - Records and Datastores](#example-usage---records-and-datastores)) against whatever system stores previous records - the validator doesn't care where either one lives.

A small wrapper class then ties `validate_record`'s output together with these two pieces: for each validation error it resolves a code via the error code map, looks up that code's message via the error message store, and falls back to the validator's own default message when no custom code or message is available, so an error is never silently dropped. Note that some custom NACC rules (e.g. `temporalrules`, `compatibility`) can report more than one failed condition for a single field - `error.info` carries the extra context needed to tell those conditions apart if you need a different message per condition.

`docs/mapping_errors_example.py` is a self-contained, runnable example of this pattern. It defines an `ErrorMessageStore` abstract class, a trivial in-memory implementation of it, and an `ErrorCodeMapper` wrapper class whose `map_errors` method turns validator output into a list of `MappedError` objects:

```python
@dataclass
class MappedError:
    error_code: str
    field: str
    value: str
    message: str
    ptid: Optional[str]
    visitnum: Optional[str]
    visitdate: Optional[str]


class ErrorCodeMapper:
    def map_errors(
        self, error_tree, default_errors: Dict[str, List[str]]
    ) -> List[MappedError]:
        ...
```

Example usage:

```bash
python3 mapping_errors_example.py
# MappedError(error_code='UDS-AGE-001', field='age', value='130',
#     message='Age must not be greater than 120.', ptid='PatientID1',
#     visitnum=3, visitdate='2025-01-01')
```

You can download the NACC-published JSON rule definitions and the respective code mapping schemas for each module from the [NACC Published Error Checks](https://docs.naccdata.org/edc/data-quality-processing/nacc-published-checks#json-rule-definitions) page. See [NACC Published JSON Rule Definitions for Form Data Validation](#nacc-published-json-rule-definitions-for-form-data-validation) above for more details.
