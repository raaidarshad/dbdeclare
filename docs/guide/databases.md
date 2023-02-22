# Databases

First, we'll go over basics and examine the `Database` class. Then, we'll start
to build our example. You can also [skip ahead](#example) to the example.

## The class

You can import `Database` like so:

```Python
{!./docs_src/guide/databases.py[ln:1]!}
```

`Database` is a representation of a [Postgres database](https://www.postgresql.org/docs/current/managing-databases.html).
It is a cluster-wide entity. This means each database in your cluster must have a unique name. The `__init__` args
correspond to the SQL `CREATE DATABASE` arguments found in the [Postgres documentation](https://www.postgresql.org/docs/current/sql-createdatabase.html).

Take a look at the class docstrings for more detail, like an explanation of the `__init__` args, the various
methods defined, what classes it inherits from, and more.

## Example

Let's start building our example. We need a database for each stage, so let's create a function
that takes a stage (like `dev` or `prod`) as input and defines a database with it:

```Python
{!./docs_src/guide/databases.py[ln:1-6]!}
```

This imports the `Database` class, defines a function `define_stage` that accepts a string name of a stage,
and defines a `Database` with the stage as the name. Now let's define a main function that creates all three
stages we want to create:

```Python hl_lines="8-11"
{!./docs_src/guide/databases.py[ln:1-12]!}
```

Here, we add a `main` function with no inputs, define a list of desired stages, loop over them, and run the
`define_stage` function for each stage.

You can run the entire file:

```Python
{!./docs_src/guide/databases.py!}
```

This defines all three databases. Excellent! Note that we haven't created anything in our cluster yet, we have only
defined our databases in code. We'll get to creation, but first let's [add some roles](/guide/roles).