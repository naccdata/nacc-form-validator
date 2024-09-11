# NACC Form Validator

Data quality rules validation module for NACC form data.

The validator is based on the [Cerberus](https://docs.python-cerberus.org/en/stable/index.html) python library, which allows validating data using quality rules defined as data. 
See the [Cerberus usage examples](https://docs.python-cerberus.org/en/stable/usage.html) for more detail.

## Table of Contents

* [Setup](#setup)
    * [Installing Pants](#installing-pants)
    * [Building a Distribution](#building-a-distribution)
    * [Common Build Issues](#common-build-issues)
* [Using the NACCValidator](#using-the-nacc-validator)

## Setup

Before getting started, it is recommended to do your installations and work in a [virtual environment](https://www.geeksforgeeks.org/python-virtual-environment/). You can set one up with the following command:

```
# create; you want to use a Python version that matches the interpreter specified in pants.toml, which in this case is Python 3.11
python3.11 -m venv path/to/your/venv

# activate
source path/to/your/venv/bin/activate

# deactivate
deactivate
```

Next, you'll need to get the distribution for this package. The strategies to use the package defined in this repository are to

1. clone the repository and [build a distribution](#building-a-distribution) locally, or
2. reference a distribution attached to a [release](https://github.com/naccdata/nacc-form-validator/releases) on GitHub.

Once you have the distribution, you can install it with

```
pip3 install dist/nacc_form_validator-VERSION-py3-none-any.whl
```

### Installing Pants

This repository is setup to use [pants](pantsbuild.org) for developing and building the distributions.

Install pants with one of the following. See [Installing Pants](https://www.pantsbuild.org/stable/docs/getting-started/installing-pants) for more information.

For Linux:
```bash
bash get-pants.sh
```

For macOS:

```bash
brew install pantsbuild/tap/pants
```

You will need to make sure that you have a Python version compatible with the interpreter set in the `pants.toml` file.

The repo has a VSCode devcontainer configuration that ensures a compatible Python is available.
You need [Docker](https://www.docker.com) installed, and [VSCode](https://code.visualstudio.com) with Dev Containers enabled.
For this follow the [Dev Containers tutorial](https://code.visualstudio.com/docs/devcontainers/tutorial) to the point of "Check Installation".

### Building a Distribution

Once pants is installed, the command 

```bash
pants package nacc_form_validator:dist
```

will then build sdist and wheel distributions in the `dist` directory.

> The version number on the distribution files is set in the `validator/BUILD` file.

### Common Build Issues

#### Incompatible Python Interpreter

If you do not have a Python version compatible with the interpreter set in the `pants.toml` file, it will fail with something similar to the following when trying to build the distribution:

```
Examined the following interpreters:
1.)    /opt/homebrew/Cellar/python@3.12/3.12.5/Frameworks/Python.framework/Versions/3.12/bin/python3.12 CPython==3.12.5
2.) /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9 CPython==3.9.6

No interpreter compatible with the requested constraints was found:

  Version matches CPython==3.11.*
```

As mentioned earlier, you can use a VSCode devcontainer configuration. Otherwise, you need to set up an environment (preferably a virtual one) with the correct Python version (in this case, Python 3.11).

#### macOS Incompatible Architecture

On macOS, if you see a long error that ends with the following when trying to build the distribution:

```
(mach-o file, but is an incompatible architecture (have 'x86_64', need 'arm64e' or 'arm64'))
```

make sure that the `pants_version` in `pants.toml` is `>=2.22.0`.


## Using the NACCValidator

There are two ways to use the NACC Form Validator:

1. Importing the `NACCValidator` class (`from nacc_form_validator import NACCValidator`) and using the class directly, or
2. Using the `run_nacc_validator.py` script
