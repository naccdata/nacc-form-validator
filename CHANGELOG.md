# Changelog

Documentation of release versions of `nacc-form-validator`

## Unreleased

* Refactors `utils.compare_values` and validation of min/max
* Reformats repo to pass `pants lint ::` and `pants check ::`
* Updates lockfile

## 0.5.3

* Fixes rounding on GDS prorated scores when it's exactly 0.5 (needs to round up, not down)
* Updates wording of error to allow NOGDS to be 0

## 0.5.2

* Handle error when birth date cannot be generated

## 0.5.1

* Adds prorated scoring back to `_check_with_gds` 
* Updates `_score_variables` to accept a `calc_var_name` variable to define the key to store the calculation under

## 0.5.0

* Adds new `function` rule `_score_variables` to handle scoring-related rules (e.g. C2F plausibility)

## 0.4.1

* Updates JSON logic's `soft_equals` and util's `compare_values` to compare two floats for equality with a precision tolerance of 0.01
	* Note this only compares with precision tolerance on explicit equals, e.g. `==` or `!=` and not `<=` and `>=`
* Fixes bug where the rule index was not being passed for a `temporalrules` error if no previous record was found

## 0.4.0

* Adds `_check_adcid` method to validate a provided ADCID against current list of ADCIDs. (Actual validation should be implemented by overriding the `is_valid_adcid` method in Datastore class)
* Adds `get_previous_record` method to grab previous record from Datastore, which can grab the previous record or the previous record where a specific field is non-empty
* Adds support for comparing against the previous record in `compare_with`
* Adds new rule `compare_age` to handle rules that need to compare ages relative to a date
* Adds custom operator `count_exact` to `json_logic.py`
* Updates `_check_subschema_valid` to accept an optional record parameter, defaults to the document - used for rules that require the previous record
* Updates `_validate_compute_gds` to remove partial GDS score calculation
* Updates `_validate_compare_with` to support the `abs` operator
* Updates `_validate_compatibility` error message to be more verbose
* Updates `_validate_temporalrules` to also support `ignore_empty` and `swap_order` parameters
* Refactors the tests to be more modularized so that they're more manageable
* Refactors logic for `compare_values` by moving it to its own utility method and allows comparing to null values
* Fixes issue where `datastore` was not being set for the temp validator in `_check_subschema_valid`, causing nested conditions with previous records to not evaluate correctly
* Overrides `_validate_nullable` method to drop custom rule definitions that cannot be evaluated for null values

## 0.3.0

* Adds `_check_with_rxnorm` function to check whether a given Drug ID is valid RXCUI code. (Actual validation should be implemented by overriding the `is_valid_rxcui` method in Datastore class)
* Updates `_validate_compare_with` to allow adjustments to be another field, and for base values to be hardcoded values
* Updates json_logic `less` function to handle None
* Updates `_validate_temporalrules` to iterate on multiple fields for `previous` and `current` clauses, remove `orderby` attribute
* Updates `_check_with_gds` function to `_validate_compute_gds` and update GDS score validation
* Fixes a bug in min/max validation wrt current_year

## 0.2.0

* Adds documentation/user guides and testing
* Adds this CHANGELOG
* Updates `_validate_compatibility` to iterate on multiple fields for `then` and `else` clauses, similar to how the `if` clause was handling it
* Updates `cast_record` to set any missing fields to `None`
* Updates `pants_version` in `pants.toml` to `2.22.0` (latest) to support building on macOS
* Renamed `validator` to `nacc_form_validator` for a more unique namespace, and imported `QualityCheck` into `__init__.py` for easier access

## 0.1.1 and older

* Initial versions
