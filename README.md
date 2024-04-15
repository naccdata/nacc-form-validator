# NACC Form Validator

Data quality rules validation module for NACC form data.

The validator is based on the [Cerberus](https://docs.python-cerberus.org/en/stable/index.html) python library, which allows validating data using quality rules defined as data. 
See the [Cerberus usage examples](https://docs.python-cerberus.org/en/stable/usage.html) for more detail.

## Using the package

The strategies to use the package defined in this repository are to 

1. clone the repository and [build a distribution](#building-a-distribution) locally, or
2. reference a distribution attached to a [release](https://github.com/naccdata/nacc-form-validator/releases) on GitHub.

## Developer guide

### Setup

This repository is setup to use [pants](pantsbuild.org) for developing and building the distributions.

Install pants with the command

```bash
bash get-pants.sh
```

You will need to make sure that you have a Python version compatible with the interpreter set in the `pants.toml` file.

The repo has a VSCode devcontainer configuration that ensures a compatible Python is available.
You need [Docker](https://www.docker.com) installed, and [VSCode](https://code.visualstudio.com) with Dev Containers enabled.
For this follow the [Dev Containers tutorial](https://code.visualstudio.com/docs/devcontainers/tutorial) to the point of "Check Installation".

### Building a distribution

Once pants is installed, the command 

```bash
pants package validator:dist
```

will then build sdist and wheel distributions in the `dist` directory.

> The version number on the distribution files is set in the `validator/BUILD` file.
