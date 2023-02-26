# Contributing

We'd love to see folks contribute! Below you will find instructions to:

- Set up the environment and pre-commit
- Run type checking and tests
- Develop DbDeclare
- Develop documentation
- Git flow

## Prerequisites

### Python

Make sure you have the right version on your machine. You can install
[pyenv](https://github.com/pyenv/pyenv#installation) then use it to install the desired version if needed:

```
> pyenv install 3.11.0
```

Please refer to the [pyenv usage](https://github.com/pyenv/pyenv#usage) instructions for more information on that tool.

### Database

You need a functioning database instance/cluster and drivers for the database you choose. DbDeclare currently only
supports Postgres.

#### Postgres

An easy way to set up Postgres on your machine is to do so via [Docker](https://docs.docker.com/get-docker/).
Once you have it set up on your machine, you can pull the [official Postgres image](https://hub.docker.com/_/postgres),
run it locally, and port-forward it:

```
> docker run --rm --name postgres -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:5432:5432/tcp postgres
```

This will spin up a Postgres instance with the following properties:

- host: `127.0.0.1`
- port: `5432`
- admin username: `postgres`
- admin password: `postgres`
- default database name: `postgres`

Note that if there is already something running on port `5432`, this will fail. You need to stop whatever process is
running there, or change the port-forward statement to a different port (`5433:5432` would forward to port `5433`, for
example).

To "restart" the instance, you can simply `ctrl-C` and run the command again.

## Setup

With prerequisites in place, we can start setting up the project for development.

### Environment

We use [Poetry](https://python-poetry.org/) to build, package, and publish the project. You can find installation
instructions for Poetry [here](https://python-poetry.org/docs/#installation).

Once Poetry is installed, you can install the project and dependencies from the root directory:

```
> poetry install
```

You might run into an issue with [psycopg](https://www.psycopg.org/psycopg3/) installation. For development, we use the
[pure Python installation](https://www.psycopg.org/psycopg3/docs/basic/install.html#pure-python-installation), which
has some requirements. If you have trouble getting it to work, you can always use the
[binary installation](https://www.psycopg.org/psycopg3/docs/basic/install.html#binary-installation) instead.

### Pre-commit

We use [pre-commit](https://pre-commit.com/) for consistent code formatting. Our configuration includes other tools
like [black](https://black.readthedocs.io/), [isort](https://pycqa.github.io/isort), and
[flake8](https://flake8.pycqa.org/). Check out [this blog post](https://www.raaid.xyz/posts/tech/learning2) to learn
more.

The configuration for pre-commit lives in the `.pre-commit-config.yaml` file, and the configuration for the other tools
exists in a combination of `tox.ini` and `pyproject.toml`.

Pre-commit is installed as a development dependency. To install the configuration in your local environment, run:

```
> pre-commit install
```

This will now run all the configured tools every time you attempt to commit your code. If there is a repeated failure,
you will need to adjust your changes; the error messages are specific and helpful, they should guide you to the issue.

To run the tools manually, you can:

```
> pre-commit run --all-files
```

## Develop DbDeclare

### Type checks

We use [mypy](https://mypy.readthedocs.io/en/stable/) for type checking. We configure it in the `pyproject.toml` file.
You can run it on the default setting (which checks all files) by simply running `mypy` from the root of the project.
Running mypy is also the first step of the continuous integration (CI) process, so when you make a pull request, it
will be automatically type-checked. The type checking must succeed for the pull request to be accepted.

### Tests

We use [pytest](https://docs.pytest.org/) for running tests. Some tests (most integration tests and some documentation
tests) require a running Postgres instance with the following characteristics:

- host: `127.0.0.1`
- port: `5432`
- username: `postgres`
- password: `postgres`
- database name: `postgres`

As mentioned [earlier](#postgres), an easy way to do this is via Docker:

```
> docker run --rm --name postgres -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:5432:5432/tcp postgres
```

Once that is running, in a seperate shell window, you can run:

```
> pytest tests
```

You can use all the standard `pytest` syntax to specify tests. Some common specifications might be to only run
unit tests, integration tests, or documentation tests. These are split up by path, so you can run `pytest tests/unit`
to run all unit tests.

Running tests is also part of the CI process. When you make a pull request, all tests will run, and they must pass in
order to be accepted.

### Develop documentation

We use [mkdocs](https://www.mkdocs.org/) specifically with the
[material theme](https://squidfunk.github.io/mkdocs-material/) to build our documentation. The configuration for it
lives in `mkdocs.yml`, and the dependencies are specified in the docs group in the `pyproject.toml`
file. The markdown all resides in the `docs` directory, and the larger code examples used throughout are in `docs_src`.
Refer to the [mkdocs documentation](https://www.mkdocs.org/user-guide/) for more detail if needed, but to serve it
locally at `localhost:8000`, you can simply run:

```
> mkdocs serve
```

## Git flow

We follow a fairly standard git workflow that has been documented plenty of times elsewhere.
[Here](https://github.com/asmeurer/git-workflow) is a great explanation of it.

Once a change is reviewed, approved, and merged, the maintainers will create a release and publish a new version of
the package.
