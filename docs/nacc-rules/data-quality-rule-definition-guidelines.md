# Data Quality Rule Definition Guidelines

Documentation adapted from [here](https://github.com/naccdata/uniform-data-set/blob/main/rules/Data%20Quality%20Rule%20Definition%20Guidelines.pdf)

## Table of Contents

* [Introduction](#introduction)
* [Validation Rules](#validation-rules)
* [Custom Rules Defined for UDS](#custom-rules-defined-for-uds)
    * [compare_with](#compare_with)
    * [compatibility](#compatibility)
    * [logic](#logic)
    * [temporalrules](#temporalrules)

## Introduction

The form validator uses QC rules defined as JSON or YAML data objects to check data, based on [Cerberus](https://docs.python-cerberus.org/en/stable/index.html). In a nutshell:

* Validation schemas are dictionaries of key-value pairs which can be specified using YAML or JSON formats (NACC rules use JSON)
* Rule definitions are organized by forms. For each form, we have provided a JSON file listing the validation rules for the variables in that form in this directory (`docs/nacc-rules`)
* Data records collected (converted to Python `dict`s) will be evaluated against the validation schema

**Example:**

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th>
<tr>
<td>

```yaml
ptid:
  type: integer
  required: true

birthmo:
  type: integer
  required: true
  min: 1
  max: 12
```
</td>
<td>

```json
{
    "ptid": {
        "type": "integer",
        "required": true
    },
    "birthmo": {
        "type": "integer",
        "required": true,
        "min": 1,
        "max": 12
    }
}
```
</td>
</table>

When validating:

```
{"ptid": 101, "birthmo": 12}    # passes validation
{"ptid": 102, "birthmo": 15}    # fails validation
{"ptid": 103}                   # fails validation
```

## Validation Rules

Check the full list of built-in Cerberus rules [here](https://docs.python-cerberus.org/validation-rules.html).

Keywords frequently used in UDS rules are described in the table below:

<table width="100%">
<tr>
<th> Keyword </th> <th> Description </th> <th width="50%"> Example </th>
<tr>
<td> allowed </td>
<td> Specify the list of allowed values. Validation will fail if any other value is given in the data record. </td>
<td>

```python
schema = {
    "limit": {
        "type": "integer",
        "allowed": [-1, 10, 100]
    }
}

data = {"limit": 10}    # passes
data = {"limit": 20}    # fails
```

</td>
</tr>
<tr>
<td> forbidden </td>
<td> Specify the list of forbidden values. Validation will fail if values in this list are included in the record. </td>
<td>

```python
schema = {
    "user": {
        "type": "string",
        "forbidden": ["viewer", "editor"]
    }
}

data = {"user": "admin"}    # passes
data = {"user": "viewer"}   # fails
```

</td>
</tr>
<tr>
<td> min, max </td>
<td> Minimum and maximum value allowed (only applicable to object types which support comparison operations like integers or floats). Each keyword can be used independently. Use together to define a range. </td>
<td>

```python
schema = {
    "length": {
        "type": "float",
        "min": 10.5,
        "max": 20.5
    }
}

data = {"length": 14}       # passes
data = {"length": 20.8}     # fails
```

</td>
</tr>
<tr>
<td> nullable </td>
<td> If set to "true", the field value is allowed to be empty. This rule will be checked on every variable, regardless of if it's defined or not. The rule's constraints defaults it to "false". </td>
<td>

```python
schema = {
    "country": {
        "type": "string",
        "nullable": true
    }
}

data = {"country": "USA"}   # passes
data = {"country": ""}      # passes

schema = {
    "country": {
        "type": "string"
    }
}

data = {"country": ""}      # fails
```

</td>
</tr>
<tr>
<td> required </td>
<td> If set to "true", the field is mandatory. Validation will fail when it is missing. </td>
<td>

```python
schema = {
    "name": {
        "type": "string",
        "required": true
    },
    "age": {
        "type": integer,
        "nullable": true
    }
}

data = {"name": "Steve", "age": 50}     # passes
data = {"name": "Debby"}                # passes
data = {"age": 40}                      # fails
```

</td>
</tr>
<tr>
<td> type </td>
<td> Data type allowed for the value. See the <a href="https://docs.python-cerberus.org/validation-rules.html">Cerberus documentation for the list of type names</a>. If multiple types are allowed, you can specify the types as a list. </td>
<td>

```python
schema = {
    "limit": {
        "type": "integer"
    }
}

data = {"limit": 10}        # passes
data = {"limit": 11.5}      # fails

schema = {
    "limit": {
        "type": ["integer", "float"]
    }
}

data = {"limit": 10}        # passes
data = {"limit": 11.5}      # passes
data = {"limit": "one"}     # fails
```

</td>
</tr>
<tr>
<td> anyof </td>
<td> Allows to define different sets of rules to validate against, supplied in a list of dicts. Field will be considered valid if any of the provided constraints validates the field. </td>
<td>

```python
schema = {
    "age": {
        "type": "integer",
        "anyof": [
            {
                "min": 0,
                "max": 120
            },
            {
                "allowed": [999]
            }
        ]
    }
}

data = {"age": 40}      # passes
data = {"age": 999}     # passes
data = {"age": 200}     # fails
```

</td>
</tr>
<tr>
<td> regex </td>
<td> Regex to validate against; only valid for string values. </td>
<td>

```python
schema = {
    "email": {
        "type": "string",
        "regex": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$ "
    }
}

data = {"email": "john@example.com"}            # passes
data = {"email": "john_at_example_dot_com"}     # fails
```

</td>
</tr>
</table>

## Custom Rules Defined for UDS

These are defined in the `NACCValidator` class.

### compare_with

Used to constrain based on comparison with another value, with optional adjustments.

* `comparator`: The comparison expression; can be one of `[">", "<", ">=", "<=", "==", "!="]`
* `base`: The value to compare to
* `adjustment`: The adjustment value to make to the base expression, if any. If specified `op` must also be provided 
* `op`: The operation to make the adjustment for; can be one of `["+", "-", "*", "/"]`. If specified, `adjustment` must also be provided

The value to compare to (`base`) can be another field in the schema OR one of the four special keywords related to the current date (i.e. the exact time/date at time of validation).

* `current_date`: Compare to the current date
* `current_year`: Compare to the current year
* `current_month`: Compare to the current month
* `current_day`: Compare to the current day

The rule definition for `compare_with` should follow the following format:

```json
{
    "<variable_name>": {
        "compare_with": {
            "comparator": "comparator, one of >, <, >=, <=, ==, !=",
            "base": "value to compare variable_name to",
            "adjustment": "(optional) the adjustment value",
            "op": "operation, one of +, -, *, /"
        }
}
```

**Example:**

`birthyr <= current_year - 15`, e.g. `birthyr` must be at least 15 years prior to the current year.

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th>
<tr>
<td>

```yaml
birthyr:
  type: integer
  required: true
  compare_with:
    comparator: "<="
    base: current_year
    adjustment: 15
    op: "-"
```
</td>
<td>

```json
{
    "birthyr": {
        "type": "integer",
        "required": true,
        "compare_with": {
            "comparator": "<=",
            "base": "current_year",
            "adjustment": 15,
            "op": "-"
        }
    }
}
```
</td>
</table>


### compatibility

Used to specify the list of compatibility constraints for a given variable with other variables within the form or across multiple forms.

Each constraint specifies `if` and `then` attributes to allow the application of a subschema based on the outcome of another schema (i.e. when the schema defiend under `if` evaluates to true for a given record, then the schema specified under `then` will be evaluated).

The rule definition for `compatibility` should follow the following format:

```json
{
    "<variable_name>": {
        "compatibility": [
            {
                "if": {
                    "subschema_attribute": "subschema to be satisifed for other variables"
                },
                "then": {
                    "subschema_attribute": "conditions to be satisifed for the current variable"
                }
            },
            {
                "if": {
                    "subschema_attribute": "subschema to be satisifed for other variables"
                },
                "then": {
                    "subschema_attribute": "conditions to be satisifed for the current variable"
                }
            }
        ]
    }
}
```

**Examples:**

If variable `incntmod` (primary contact mode with participant) is 6, then variable `incntmdx` (specify primary contact mode with participant) cannot be blank. 

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th>
<tr>
<td>

```yaml
incntmdx:
  type: string
  nullable: true
  compatibility:
    - if:
        incntmod:
          allowed:
            - 6
      then:
        nullable: false
```
</td>
<td>

```json
{
    "incntmdx": {
        "type": "string",
        "nullable": true,
        "compatibility": [
            {
                "if": {
                    "incntmod": {
                        "allowed": [6]
                    }
                },
                "then": {
                    "nullable": false
                }
            }
        ]
    }
}
```
</td>
</table>

This rule can also be used to define the "if not, then" case. For this, we use `forbidden` instead of `allowed`.

So if variable `incntmod` (primary contact mode with participant) is NOT 6, then variable `incntmdx` (specify primary contact mode with participant) must be blank.

 <table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th>
<tr>
<td>

```yaml
incntmdx:
  type: string
  nullable: true
  compatibility:
    - if:
        incntmod:
          forbidden:
            - 6
      then:
        nullable: true
        filled: false
```
</td>
<td>

```json
{
    "incntmdx": {
        "type": "string",
        "nullable": true,
        "compatibility": [
            {
                "if": {
                    "incntmod": {
                        "forbidden": [6]
                    }
                },
                "then": {
                    "nullable": true,
                    "filled": false
                }
            }
        ]
    }
}
```
</td>
</table>


### logic

Used to specify a mathematicaal formula/expression to validate against, and utilizes [json-logic-py](https://github.com/nadirizr/json-logic-py) (saved as `json_logic.py`). This rule overlaps with `compare_with`, but allows for comparison between multiple variables, as opposed to just two (and does not account for special keywords).

* `formula`: The mathematical formula/expression to apply; see the `operations` dict in `json_logic.py` to see the full list of available operators. Each operator expects differently formatted arguments
* `errormsg`: A custom message to supply if validation fails. This key is optional; if not provided the error message will simply be `value {value} does not satisify the specified formula`

The rule definition for `logic` should follow the following format:

```json
{
    "<variable_name>": {
        "logic": {
            "formula": {
                "operator": "list of arguments for the operator"
            },
            "errormsg": "<optional error message to supply if validation fails>"
        }
}
```

**Example:**

One of `var1`, `var2`, or `var3` must be `1`.

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th>
<tr>
<td>

```yaml
var1:
  type: integer
  nullable: true

var2:
  type: integer
  nullable: true

var3:
  type: integer
  nullable: true
  logic:
    formula:
      or:
        - ==:
            - 1
            - var: var1
        - ==:
            - 1
            - var: var2
        - ==:
            - 1
            - var: var3
```
</td>
<td>

```json
{
    "var1": {
        "type": "integer",
        "nullable": true,
    },
    "var2": {
        "type": "integer",
        "nullable": true,
    },
    "var3": {
        "type": "integer",
        "nullable": true,
        "logic": {
            "formula": {
                "or": [
                    {
                        "==": [1, {"var": "var1"}]
                    },
                    {
                        "==": [1, {"var": "var2"}]
                    },
                    {
                        "==": [1, {"var": "var3"}]
                    }
                ]
            }
        }
    }
}
```
</td>
</table>

### temporalrules

Used to specify the list of longitudinal checks for a given variable.

* `orderby` specifies the variable name to order the longitudinal records.
* `constraints` specifies the list of checks to be performed on the previous records. Each constraint specifies `previous` and `current` attributes to allow the application of a subschema based on the outcome of another schema.

The rule definition for `temporalrules` should follow the following format:

```json
{
    "<variable_name>": {
        "temporalrules": {
            "orderby": "<variable to order the records by>",
            "constraints": [
                {
                    "previous": {
                        "subschema_attribute": "subschema to be satisfied for the previous record"
                    },
                    "current": {
                        "subschema_attribute": "subschema to be satisfied for the current record"
                    }
                },
                {
                    "previous": {
                        "subschema_attribute": "subschema to be satisfied for the previous record"
                    },
                    "current": {
                        "subschema_attribute": "subschema to be satisfied for the current record"
                    }
                }
            ]
        }
}
```

**Example:**

If variable `taxes` (difficulty with taxes, business, and other papers) is 0 (normal) at a previous visit, then `taxes` cannot be 8 (not applicable/never did) at the follow-up visit.

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th>
<tr>
<td>

```yaml
taxes:
  type: integer
  temporalrules:
    orderby: visit_date
    constraints:
      - previous:
          allowed:
            - 0
        current:
          forbidden:
            - 8
```
</td>
<td>

```json
{
    "taxes": {
        "type": "integer",
        "temporalrules": {
            "orderby": "visit_date",
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
```
</td>
</table>
