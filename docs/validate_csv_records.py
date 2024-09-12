#!/usr/bin/env python3
"""
Example script of how you may set up a CLI to read in a CSV file containing multiple records
to validate against a schema also passed in as a JSON. It writes the errors (if any) to a CSV
file if specified (otherwise writes to stdout), which the user can then use to fix the forms.
"""
import argparse
import csv
import json
import logging

from pathlib import Path
from nacc_form_validator import QualityCheck

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--rules-json', dest="rules_json", type=Path, required=True,
                        help='A JSON file containing the schema to validate on; should be compliant with expected NACC rules')
    parser.add_argument('-i', '--input-records-csv', dest="input_records_csv", type=Path, required=True,
                        help='A CSV containing records (one per row) to validate against the schema')

    parser.add_argument('-o', '--output-errors', dest="output_errors", type=Path, required=False,
                        help='The output CSV or JSON to write errors to. If not provided, results will just be written to stdout')
    parser.add_argument('-s', '--disable-strict', dest="disable_strict", action="store_true", default=False,
                        help='Disable strict mode - validator will skip unknown forms/fields')

    args = parser.parse_args()

    log.info("Arguments:")
    log.info(f"rules_json:\t{args.rules_json}")
    log.info(f"input_records_csv:\t{args.input_records_csv}")
    log.info(f"output_errors:\t{args.output_errors}")
    log.info(f"strict mode::\t{not args.disable_strict}")

    if not args.rules_json.is_file():
        raise FileNotFoundError(f"Cannot find specified rules JSON: {args.rules_json}")
    if not args.input_records_csv.is_file():
        raise FileNotFoundError(f"Cannot find specified input records CSV: {args.input_records_csv}")

    """
    Instantiate the quality check object from rules JSON. This script assumes no datastore, and therefor
    no plausibility checks (and no need for `pk_name`, so a dummy one is provided).
    If you need one, you'll need to create and instantiate it before creating the QualityControl, and
    update the script to pass in a primary key.
    """
    rules = None
    with args.rules_json.open('r') as fh:
        rules = json.load(fh)

    qc = QualityCheck("primary_key", rules, strict=not args.disable_strict)

    """
    Validate records, and collect all the errors
    """
    all_errors = []
    error_headers = set(['row'])
    with args.input_records_csv.open('r') as fh:
        reader = csv.DictReader(fh)
        headers = {x: {} for x in reader.fieldnames}

        # start at "row 1" since ignoring headers
        for i, record in enumerate(reader, 1):
            passed, _, errors, _ = qc.validate_record(record)
            if not passed:
                errors['row'] = i
                all_errors.append(errors)
                error_headers.update(set(errors.keys()))
                log.warning(f"Row {i} in the input records CSV failed validation")

    """
    Convert all_errors and error_headers to a "csv-like" dict for writing/printing out
    """
    for error in all_errors:
        for header in error_headers:
            if header not in error:
                error[header] = ''

    # sort but make sure row is first
    error_headers = list(error_headers)
    error_headers.sort()
    error_headers.insert(0, error_headers.pop(error_headers.index('row')))

    if args.output_errors:
        suffix = args.output_errors.suffix
        if suffix == ".json":
            with args.output_errors.open('w') as outfh:
                errors_json = {error.pop('row'): error for error in all_errors}
                json.dump(errors_json, outfh, indent=4)
        elif suffix in ['.csv', '']:
            with args.output_errors.open('w') as outfh:
                writer = csv.DictWriter(outfh, error_headers)
                writer.writeheader()
                writer.writerows(all_errors)
        else:
            raise ValueError(f"Unsupported output suffix: {suffix}")
    else:
        log.info(f"The following rows failed validation: ")
        for error in all_errors:
            print(f"Row {error.pop('row')}: {json.dumps(error, indent=4)}")

    log.info(f"{len(all_errors)} records failed validation")
