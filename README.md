# postgres-declare

<!-- [![Release](https://img.shields.io/github/v/release/raaidarshad/postgres-declare)](https://img.shields.io/github/v/release/raaidarshad/postgres-declare) -->
<!-- [![Build status](https://img.shields.io/github/workflow/status/raaidarshad/postgres-declare/merge-to-main)](https://img.shields.io/github/workflow/status/raaidarshad/postgres-declare/merge-to-main) -->

[![Python version](https://img.shields.io/badge/python_version-3.11-blue)](https://github.com/psf/black)
[![Code style with black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)
[![More style with flake8](https://img.shields.io/badge/code_style-flake8-blue)](https://flake8.pycqa.org)
[![Imports with isort](https://img.shields.io/badge/%20imports-isort-blue)](https://pycqa.github.io/isort/)
[![Type checking with mypy](https://img.shields.io/badge/type_checker-mypy-blue)](https://mypy.readthedocs.io)
[![License](https://img.shields.io/github/license/raaidarshad/postgres-declare)](https://img.shields.io/github/license/raaidarshad/postgres-declare)

Declarative layer for everything Postgres.

## Usage

TODO: Describe how to use your project!
TODO: Do you need an installation, contributing, community, documentation, or other section here?
Depends on the project, make sure to add it if it makes sense to do so.

## Development

This project uses [Poetry](https://python-poetry.org/) to manage dependencies. It also helps with pinning dependency and python
versions. We also use [pre-commit](https://pre-commit.com/) with hooks for [isort](https://pycqa.github.io/isort/),
[black](https://github.com/psf/black), and [flake8](https://flake8.pycqa.org/en/latest/) for consistent code style and
readability. Note that this means code that doesn't meet the rules will fail to commit until it is fixed.

We use [mypy](https://mypy.readthedocs.io/en/stable/index.html) for static type checking. This can be run [manually](#run-static-type-checking),
and the CI runs it on PRs to the `main` branch. We also use [pytest](https://docs.pytest.org/en/7.2.x/) to run our tests.
This can be run [manually](#run-tests) and the CI runs it on PRs to the `main` branch.

### Setup

1. [Install Poetry](https://python-poetry.org/docs/#installation).
2. Run `poetry install --no-root`
3. Run `source $(poetry env list --full-path)/bin/activate && pre-commit install && deactivate` to set up `pre-commit`

You're all set up! Your local environment should include all dependencies, including dev dependencies like `black`.
This is done with Poetry via the `poetry.lock` file.

### Run Code Format and Linting

To manually run isort, black, and flake8 all in one go, simply run `pre-commit run --all-files`. Explore the `pre-commit` docs (linked above)
to see more options.

### Run Static Type Checking

To manually run mypy, simply run `mypy .` from the root directory of the project. It will use the default configuration
specified in `pyproject.toml`.

### Update Dependencies

To update dependencies in your local environment, make changes to the `pyproject.toml` file then run `poetry update` from the root directory of the project.

### Run Tests

To manually run rests, simply run `pytest tests` from the root directory of the project. Explore the `pytest` docs (linked above)
to see more options.
