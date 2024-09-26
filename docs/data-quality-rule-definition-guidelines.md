# Data Quality Rule Definition Guidelines

## Table of Contents

* [Introduction](#introduction)
* [Validation Rules](#validation-rules)
* [Custom Rules Defined for UDS](#custom-rules-defined-for-uds)
    * [compare_with](#compare_with)
    * [compatibility](#compatibility)
    * [logic](#logic)
    * [temporalrules](#temporalrules)

## Introduction

The form validator uses QC rules defined as JSON or YAML data objects to check data, based on [Cerberus](https://docs.python-cerberus.org/). In a nutshell:

* Validation schemas are dictionaries of key-value pairs which can be specified using YAML or JSON formats
* Rule definitions are organized by forms. For each form, a YAML or JSON file lists the validation rules for the fields in that form (NACC uses JSON)
* Data records collected (converted to Python `dict`) will be evaluated against the validation schema

**Example:**

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th> <th> When Validating </th>
<tr>
<td valign="top">

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
<td valign="top">

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
<td valign="top">

```python
{"ptid": 101, "birthmo": 12}    # passes
{"ptid": 102, "birthmo": 15}    # fails
{"ptid": 103}                   # fails
```
</td>
</table>

## Validation Rules

Check the full list of built-in Cerberus rules [here](https://docs.python-cerberus.org/validation-rules.html).

Keywords frequently used in UDS rules are described in the table below:

<table width="100%">
<tr>
<th> Keyword </th> <th> Description </th> <th width="50%"> Example </th>
<tr>
<td valign="top"> <code>allowed</code> </td>
<td valign="top"> Specify the list of allowed values. Validation will fail if any other value is given in the data record. </td>
<td valign="top">

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
<td valign="top"> <code>forbidden</code> </td>
<td valign="top"> Specify the list of forbidden values. Validation will fail if values in this list are included in the record. </td>
<td valign="top">

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
<td valign="top"> <code>min</code>, <code>max</code> </td>
<td valign="top"> Minimum and maximum value allowed (only applicable to object types which support comparison operations like integers or floats). Each keyword can be used independently. Use together to define a range. </td>
<td valign="top">

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
<td valign="top"> <code>nullable</code> </td>
<td valign="top"> If set to "true", the field value is allowed to be empty. This rule will be checked on every field, regardless of if it's defined or not. The rule's constraints defaults it to "false". In other words, if neither `nullable` nor `required` are set, the field is required. </td>
<td valign="top">

```python
schema = {
    "country": {
        "type": "string",
        "nullable": True
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
<td valign="top"> <code>required</code> </td>
<td valign="top"> If set to "true", the field is mandatory. Validation will fail when it is missing. </td>
<td valign="top">

```python
schema = {
    "name": {
        "type": "string",
        "required": True
    },
    "age": {
        "type": "integer",
        "nullable": True
    }
}

data = {"name": "Steve", "age": 50}     # passes
data = {"name": "Debby"}                # passes
data = {"age": 40}                      # fails
```

</td>
</tr>
<tr>
<td valign="top"> <code>type</code> </td>
<td valign="top"> Data type allowed for the value. See the <a href="https://docs.python-cerberus.org/validation-rules.html">Cerberus documentation for the list of type names</a>. If multiple types are allowed, you can specify the types as a list. </td>
<td valign="top">

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
<td valign="top"> <code>anyof</code> </td>
<td valign="top"> Allows to define different sets of rules to validate against, supplied in a list of dicts. Field will be considered valid if any of the provided constraints validates the field. </td>
<td valign="top">

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
<td valign="top"> <code>regex</code> </td>
<td valign="top"> Regex to validate against; only valid for string values. </td>
<td valign="top">

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

Used to validate the field based on comparison with another field, with optional adjustments.

* `comparator`: The comparison expression; can be one of `[">", "<", ">=", "<=", "==", "!="]`
* `base`: The field or value to compare to
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
    "field_name": {
        "compare_with": {
            "comparator": "comparator, one of >, <, >=, <=, ==, !=",
            "base": "field or value to compare field_name to",
            "adjustment": "(optional) the adjustment value",
            "op": "(optional) operation, one of +, -, *, /"
        }
}
```

**Example:**

`birthyr <= current_year - 15`, e.g. `birthyr` must be at least 15 years prior to the current year.

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th> <th> When Validating </th>
<tr>
<td valign="top">

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
<td valign="top">

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

<td valign="top">

```python
{"birthyr": 1995}   # passes
{"birthyr": 2030}   # fails until 2045
```
</td>
</table>

### compatibility

Used to specify the list of compatibility (if-then-else) constraints for a given field with other fields within the form or across multiple forms. A field will only pass validation if none of the compatibility constraints are violated.

Each constraint specifies `if`, `then`, and (optionally) `else` attributes to allow the validation of a set of fields/subschemas based on the outcome of other fields/subschemas (i.e. when the schema(s) defined under `if` evaluates to true for a given record, then the schema(s) specified under `then` will be evaluated).

Each `if/then/else` attribute can have several fields which need to be satisifed, with the `*_op` attribute specifying the boolean operation in which to compare the different fields. For example, if `if_op = or`, then as long as _any_ of the fields satsify their schema, the `then` attribute will be evaluated. The default `*_op` is `and`.

The rule definition for `compatibility` follows the following format:

```json
{
    "<field_name>": {
        "compatibility": [
            {
                "if": {
                    "<field_name>": "subschema to be satisifed"
                },
                "then": {
                    "<field_name>": "subschema to be satisifed"
                }
            },
            {
                "if_op": "and",
                "then_op": "or",
                "else_op": "or",

                "if": {
                    "<field_name>": "subschema to be satisifed",
                    "<field_name>": "subschema to be satisifed"
                },
                "then": {
                    "<field_name>": "subschema to be satisifed",
                    "<field_name>": "subschema to be satisifed"
                },
                "else": {
                    "<field_name>": "subschema to be satisifed",
                    "<field_name>": "subschema to be satisifed"
                }
            }
        ]
    }
}
```

One additional nuance is the evaluation against `None`/null values. Because Cerberus always evaluates `"nullable": False` by default, the application of a subschema in this case must explicitly set `"nullable": True` if the attributes evaluate or result in null values. For example

```
# if case: If PARENTVAR is blank or 88, then VAR1 must be blank
"if": {
    "parentvar": {
        "nullable": True,  # <--- external nullable flag for the if clause
        "anyof": [
            {
                "nullable": True,
                "filled": False
            },
            {
                "allowed": [88]
            }
        ]
    }
},
"then": {
    "var1": {
        "nullable": True,
        "filled": False}
}

# then case: if PARENTVAR is blank, then the following must be blank: var1, var2, var3
"if": {
    "parentvar": {
        "nullable": True,
        "filled": False
    }
},
"then": {
    "var1": {
        "nullable": True,  # <--- nullable flag for the then clause
        "logic": {
            "formula": {
                "and": [
                    {"==": [None, {"var": "var1"}]},
                    {"==": [None, {"var": "var2"}]},
                    {"==": [None, {"var": "var3"}]}
                ]
            }
        }
    }
}
```

**Examples:**

If field `incntmod` (primary contact mode with participant) is 6, then field `incntmdx` (specify primary contact mode with participant) cannot be blank. 

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th> <th> When Validating </th>
<tr>
<td valign="top">

```yaml
incntmod:
  type: integer
  required: true

incntmdx:
  type: integer
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
<td valign="top">

```json
{
    "incntmod": {
        "type": "integer",
        "required": true
    },
    "incntmdx": {
        "type": "integer",
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
<td valign="top">

```python
{"incntmod": 1, "incntmdx": None}   # passes
{"incntmod": 6, "incntmdx": 1}      # passes
{"incntmod": 6, "incntmdx": None}   # fails
```
</td>
</table>

This rule can also be used to define the "if not, then" case. For this, we use `forbidden` instead of `allowed`.

So if field `incntmod` (primary contact mode with participant) is NOT 6, then field `incntmdx` (specify primary contact mode with participant) must be blank.

 <table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th> <th> When Validating </th>
<tr>
<td valign="top">

```yaml
incntmod:
  type: integer
  required: true

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
<td valign="top">

```json
{
    "incntmod": {
        "type": "integer",
        "required": true
    },
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
<td valign="top">

```python
{"incntmod": 1, "incntmdx": None}   # passes
{"incntmod": 6, "incntmdx": 1}      # fails
{"incntmod": 6, "incntmdx": None}   # passes
{"incntmod": 1, "incntmdx": 1}      # fails
```
</td>
</table>


### logic

Used to specify a mathematical formula/expression to validate against, and utilizes [json-logic-py](https://github.com/nadirizr/json-logic-py) (saved as `json_logic.py`). This rule overlaps with `compare_with`, but allows for comparison between multiple fields, as opposed to just two (and does not account for special keywords).

* `formula`: The mathematical formula/expression to apply; see the `operations` dict in `json_logic.py` to see the full list of available operators. Each operator expects differently formatted arguments
* `errormsg`: A custom message to supply if validation fails. This key is optional; if not provided the error message will simply be `value {value} does not satisify the specified formula`

The rule definition for `logic` should follow the following format:

```json
{
    "<field_name>": {
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
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th> <th> When Validating </th>
<tr>
<td valign="top">

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
<td valign="top">

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
<td valign="top">

```python
{"var1": 1, "var2": 1, "var3": 1}            # passes
{"var1": 1, "var2": None, "var3": None}      # passes
{"var1": None, "var2": None, "var3": None}   # fails
```
</td>
</table>

### temporalrules

Used to specify the list of longitudinal checks for a given field.

* `orderby` specifies the field name to order the longitudinal records by.
* `constraints` specifies the list of checks to be performed on the previous records. Each constraint specifies `previous` and `current` attributes to allow the application of a subschema based on the outcome of another schema.

The rule definition for `temporalrules` should follow the following format:

```json
{
    "<field_name>": {
        "temporalrules": {
            "orderby": "<field to order the records by>",
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

If field `taxes` (difficulty with taxes, business, and other papers) is 0 (normal) at a previous visit, then `taxes` cannot be 8 (not applicable/never did) at the follow-up visit.

<table>
<tr>
<th> YAML Rule Definition </th> <th> JSON Rule Definition </th> <th> When Validating </th>
<tr>
<td valign="top">

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
<td valign="top">

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
<td valign="top">

```python
# assume this record already exists
# {"visit_date": 1, "taxes": 0}

{"visit_date": 2, "taxes": 1}   # passes
{"visit_date": 2, "taxes": 8}   # fails
```
</td>
</table>
