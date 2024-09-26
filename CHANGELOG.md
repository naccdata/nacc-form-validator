# Changelog

Documentation of release versions of `nacc-form-validator`

## 0.2.0

* Updates `_validate_compatibility` to iterate on multiple fields for `then` and `else` clauses, similar to how the `if` clause was handling it
* Updates `cast_record` to set any missing fields to `None`
* Updates `pants_version` in `pants.toml` to `2.22.0` (latest) to support building on macOS
* Renamed `validator` to `nacc_form_validator` for a more unique namespace, and imported `QualityCheck` into `__init__.py` for easier access
* Added documentation/user guides and testing
* Added this CHANGELOG

## 0.1.1 and older

* Initial versions
