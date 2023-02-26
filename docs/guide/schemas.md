# Schemas

First, we'll go over basics and examine the `Schema` class. Then, we'll continue
to build our example. You can also [skip ahead](#example) to the example.

## The Schema class

You can import `Schema` like so:

```Python
from dbdeclare.entities import Schema
```

`Schema` is a representation of a [Postgres schema](https://www.postgresql.org/docs/15/ddl-schemas.html).
It is a database-wide entity. This means each schema in your database (not cluster) must have a unique name.
The `__init__` args correspond to the SQL `CREATE SCHEMA` arguments found in the [Postgres documentation](https://www.postgresql.org/docs/current/sql-createschema.html).

Take a look at the class docstrings for more detail, like an explanation of the `__init__` args, the various
methods declared, what classes it inherits from, and more.

## Example

Let's keep building our example. In addition to the databases and roles we've declared, we need a `log` schema
for two tables that don't go in the default schema. We need this for each database.
Since each database corresponds to each stage, we can simply create a new schema as part
of our `declare_stage` function:

```Python hl_lines="5 17"
{!./docs_src/guide/schemas.py[ln:1-17]!}

# omitted code below
```

Note that we assign the output of our call to `Database` to a variable now (`db`) so that we
can explicitly refer to it when we create our log `Schema`. We don't need to create the default
schema, as that will already exist when a new database is created.

Entire file now:

```Python
{!./docs_src/guide/schemas.py!}
```

This code now declares the databases, roles, and schemas we need. All that's left is to declare the
tables + columns, grant privileges, then actually push all this to the cluster. Let's [add some tables](/guide/tables).