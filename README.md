# NACC Form Validator

Data quality rules validation module for NACC form data.

The validator is based on the [Cerberus](https://docs.python-cerberus.org/en/stable/index.html) python library, which allows validating data using quality rules defined as data. 
See the [Cerberus usage examples](https://docs.python-cerberus.org/en/stable/usage.html) for more detail.

## Using a distribution


## Building a distribution

First install pants with the command

```bash
bash get-pants.sh
```

The command 
```bash
pants package validator:dist
```

will then build sdist and wheel distributions in the `dist` directory.

> The version number on the distribution files is set in the `validator/BUILD` file.
