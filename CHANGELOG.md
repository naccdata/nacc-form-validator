# Changelog

Documentation of release versions of `nacc-form-validator`

## 0.3.0

* Updates `_validate_compare_with` to allow adjustments to be another field, and for base values to be hardcoded values
* Update json_logic `less` function to handle None
* Updates `_validate_temporalrules` to iterate on multiple fields for `previous` and `current` clauses, remove `orderby` attribute
* Updates `_check_with_gds` function to `_validate_compute_gds` and update GDS score validation
* Updates `_check_subschema_valid` to accept an optional record parameter, defaults to the document - used for rules that require the previous record
* Updates `compare_with` to support the `abs` operator
* Adds `_check_with_rxnorm` function to check whether a given Drug ID is valid RXCUI code.
* Adds `previous_record` as a special keyword for `__get_value_for_key`, which is used by `compare_with`
* Adds `get_previous_record` method to grab previous record from Datastore, which can grab the previous record or the previous record where a specific field is non-empty
* Adds additional tests
* Fixed a bug in min/max validation wrt current_year

## 0.2.0

* Updates `_validate_compatibility` to iterate on multiple fields for `then` and `else` clauses, similar to how the `if` clause was handling it
* Updates `cast_record` to set any missing fields to `None`
* Updates `pants_version` in `pants.toml` to `2.22.0` (latest) to support building on macOS
* Renamed `validator` to `nacc_form_validator` for a more unique namespace, and imported `QualityCheck` into `__init__.py` for easier access
* Added documentation/user guides and testing
* Added this CHANGELOG

## 0.1.1 and older

* Initial versions
