# DbDeclare

<make simple logo and put it here?>
link to GH repo
maybe this should be the same as the readme

A declarative layer for your database, built on [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy).

## Overview

### What is it?

DbDeclare is a Python package that helps you create and manage entities in your database cluster,
like databases, roles, access control, and (eventually) more. It aims to fill the gap between
SQLAlchemy (SQLA) and infrastructure as code (IaC).

TODO image of what sqlalchemy covers, what this covers, what IaC covers

### Why use it?

DbDeclare does what SQLA does but for database entities beyond tables and columns. You can:

- Define desired state in Python
- Avoid maintaining raw SQL
- Tightly integrate your databases, roles, access control, and more with your tables

Future versions will have more features, and you will be able to:

- Have version control over database changes (like [Alembic](https://github.com/sqlalchemy/alembic))
- Define upgrades/downgrades without explicitly defining the changes (like [autogen](https://alembic.sqlalchemy.org/en/latest/autogenerate.html))

Additionally, DbDeclare is:

- Typed: Type-checking done via [mypy](https://mypy.readthedocs.io/en/stable/)
- Thoroughly commented: There are docstrings for every method and class
- Well-tested: Though this is a new package under active development, solid test coverage is a high priority

Running SQL scripts before SQLA and after IaC can be messy and hard to maintain.
If you prefer to have databases, roles, and the like defined alongside your infrastructure, then there are
great tools available for that, like Terraform and Pulumi's providers for Postgres and MySQL. So if you want
it tied to that, great! But if, like me, you want it closer to your application code and alongside SQLA, this
tool likely makes more sense for you.

## Requirements

This requires a recent version of Python. Works with Python 3.11 or higher.

This also requires a compatible driver/package for your database of choice, like
[psycopg](https://www.psycopg.org/) for Postgres.

SQLAlchemy is a dependency and will be installed when you install DbDeclare. DbDeclare
works with SQLAlchemy 2.0.0 or higher.


## Installation

DbDeclare is published on [PyPi](TODO). You can install it with `pip` or any tool
that uses `pip` under the hood. This is typically installed in a [virtual environment](https://docs.python.org/3/library/venv.html).

```
> pip install db-declare
```

## Example

Here is a simple Postgres example. We will create a database and a user, and make sure the user
can connect to the database. You need a Postgres cluster/instance and a python environment.

If needed, an easy way to spin up a Postgres instance is with [Docker](https://www.docker.com/),
specifically the [official Postgres image](https://hub.docker.com/_/postgres):

```
> docker run --rm --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:5433:5432/tcp postgres
```

This spins up a Postgres instance with the default database name of `postgres`, an admin user of `postgres` with the
password `postgres`, on port `5433` to not conflict with any locally running instance.

Assuming you have a Python environment set up, DbDeclare installed, and psycopg installed (`pip install psycopg`),
you can create a database and a user that can connect to it like this:

```Python
{!./docs_src/index.py!}
```

1. Make sure this role can log in (make it a user)
2. Provide a password for the user to log in with
3. Specify that this user can connect to the `falafel` database
4. The engine to run DbDeclare must have admin privileges, so we use the `postgres` user here

After running this script, you should be able to access the `falafel` database as `hungry_user`. You can try it out with
`psql` (if you don't have it installed, find it [here](https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/)).
In a separate shell from where the docker run command is running, you can run:

```
> psql -h 127.0.0.1 -p 5433 -U hungry_user -d falafel

password for user hungry_user: ***

falafel=# 
```

Voila! Check out the [user guide](/guide) for more involved use cases.

## Contributing

Check out development, testing, and contributing guidelines [here](/contributing).

## Help or get help

Need help, or want to help out? Find out how [here](/help).

## License

This project is licensed under the terms of the [MIT license](https://github.com/raaid/db-declare/blob/main/LICENSE)