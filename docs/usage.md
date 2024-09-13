# Using the NACC Form Validator

The purpose of this package is to provide developers with ways to validate and run error checks on NACC-specific forms before submission, or for validating extra data your forms may have.

The JSON rules (validation schemas) for all NACC forms are stored under `docs/nacc-rules`, and can be modified as needed. See [Data Quality Rule Definition Guidelines](./nacc-rules/data-quality-rule-definition-guidelines.md) for more information on how the quality rules themselves work.

## Table of Contents

* [Overview](#overview)
* [Example Usage - Hello World](#example-usage---hello-world)
* [Example Usage - Records and Datastores](#example-usage---records-and-datastores)
* [Example Usage - Bulk Validation](#example-usage---bulk-validation)

## Overview

The main "entry point", or class to instantiate for validation, is `QualityCheck`, which in turn creates a `NACCValidator` to both validate the schema and return extra information from the validator. `NACCValidator` itself is an extension of [Cerberus' `Validator` class](https://docs.python-cerberus.org/api.html#cerberus.Validator). It can also use an optional `Datastore` object which you can implement to access records in your own database. See [Example Usage - Records and Datastores](#example-usage---records-and-datastores) for more information.

There isn't really any benefit to using `NACCValidator` directly, but if you decide to just keep in mind the following (e.g. duplicate what `QualityCheck` will handle for you):

* If the records you're validating on have _missing_ fields (e.g. passing an empty `dict` as a "record" as opposed to a `dict` with all fields set to `None`), some of the more complicated rules like `logic` may not entirely behave as expected. The `cast_record` resolves this by setting any missing fields (based on the schema) to `None`, **so you need to call this method before validating**
* Similarly, if using `primary_key` and `datastore`, those properties will need to be explicitly set on the `NACCValidator` object
* The `errors` property only reports the error of the _last validation that failed_, so if you want to keep track of all of them you'll need to keep track of them (an example of this is done in [Example Usage - Bulk Validation](#example-usage---bulk-validation) but more externally through `QualityCheck`)

## Example Usage - Hello World

The following is a simple example of using this package.

```python
from nacc_form_validator import QualityCheck

pk_name = "example_key"

schema = {
    "hello": {
        "type": "string",
        "required": True,
        "allowed": [
            "world"
        ]
    }
}

qc = QualityCheck(pk_name, schema, strict=True, datastore=None)

passed, sys_failure, errors, error_tree = qc.validate_record({"hello": "world"})
# passed = True
# sys_failure = False
# errors = {}
# error_tree = [],{}

passed, sys_failure, errors, error_tree = qc.validate_record({"hello": "pluto"})
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

In the previous example, we validated a single record. But you may want to compare a record against previous records associated with the same key, particularly if your schema uses temporal rules (see [Data Quality Rule Definition Guidelines](./nacc-rules/data-quality-rule-definition-guidelines.md)), which are usually associated with plausibility checks. If you are validating against a schema that doesn't have temporal rules, it isn't really necessary to set up a datastore.

This is where `pk_name` and `datastore` come in, in which `pk_name` is the "primary key" to index the datastore by. `datastore.py` provides a `Datastore` abstract class that you must implement, specifically the `get_previous_instance` method.

Say `pk_name` is the `patient_id`. For sake of simplicity, the "database" in this example will be a hard-coded Python dict, but yours will likely be much more complicated. Next our validation scheme checks to see if a patient filled out taxes in a previous visit (0); if so, the current record cannot indicate that they never did it (8).

```python
import copy

from nacc_form_validator import QualityCheck
from nacc_form_validator.datastore import Datastore


class CustomDatastore(Datastore):

    def __init__(self) -> None:
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

    def get_previous_instance(self, orderby: str, pk_field: str, current_ins: dict[str, str]) -> dict[str, str] | None:
        """
        See where this record would fit in the sorted record and return the previous instance
        Making a deep copy since we don't actually want to modify the record in this method
        """
        key = current_ins[pk_field]
        if key not in self.__db:
            return None
        
        sorted_record = copy.deepcopy(self.__db[key])
        sorted_record.append(current_ins)
        sorted_record.sort(key=lambda record: record[orderby])

        index = sorted_record.index(current_ins)
        return sorted_record[index - 1] if index != 0 else None


pk_name = "patient_id"
datastore = CustomDatastore()

schema = {
    "patient_id": {
        "type": "string"
    },
    "visit_num": {
        "type": "integer"
    },
    "taxes": {
        "type": "integer",
        "temporalrules": {
            "orderby": "visit_num",
            "constraints": [
                {
                    "previous": {
                        "allowed": [0]
                    },
                    "current": {
                        "forbidden": [8]
                    }
                }
            ]
        }
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
#                                             'orderby': 'visit_num',
#                                             'constraints': [{
#                                                 'previous': {'allowed': [0]},
#                                                 'current': {'forbidden': [8]}
#                                             }]
#                                         },
#                                         value=8,
#                                         info=(1, "('taxes', ['unallowed value 8'])",{'allowed': [0]})
#                                         )
#     ],{}
# }
```

## Example Usage - Bulk Validation

It is likely you will want to validate multiple records at once. This is easily achieved by instantiating a `QualityCheck` with the corresponding schema and pass the record(s) you want to validate as Python `dict` objects. What this data looks like outside of that is up to you - maybe you wish to read in forms from external files (JSONs, YAML, or CSVs), or directly from a database.

`docs/validate_csv_records.py` sets up an example CLI script to read in multiple records from a CSV file and validate them against a schema similarly passed as a JSON file. It then summarizes the results and prints them to a CSV or JSON file (based on file extension, defaults to CSV if no extension is provided), or `stdout` (in JSON) if no output file is specified.
