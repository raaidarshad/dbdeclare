# Tables (and columns)

Tables and columns are defined via [SQLAlchemy](https://www.sqlalchemy.org/), a proven,
robust tool that this package is built on. You can optional define tables and columns
via [SQLModel](https://sqlmodel.tiangolo.com/), a project that combines a lot of the benefits of SQLA with
[Pydantic](https://docs.pydantic.dev/), resulting in highly reusable models for both data definition and strong
typing throughout your application. In either case, you define tables and columns through
another library, then simply refer to them from DbDeclare via the `DatabaseContent` class.

We'll go over the basics and examine the `DatabaseContent` class, then we'll continue
to build our example. You can also [skip ahead](#example) to the example.

## The DatabaseContent class

You can import `DatabaseContent` like so:

```Python
from dbdeclare.entities import DatabaseContent
```

`DatabaseContent` is a wrapper around a [SQLAlchemy base](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#orm-declarative-mapping).
It is a database-wide entity, which means it must be uniquely named within a database.
The `__init__` args are a combination of inherited utility and some necessary references: you
must refer to which `Database` this content belongs to, and which schemas (if non-default) it
depends on.

Take a look at the class docstrings for more detail, like an explanation of the `__init__` args,
the various methods defined, what classes it inherits from, and more. `DatabaseContent` is slightly
odd because it does not have 1-to-1 correspondence with a Postgres entity, and many of the
internal methods call SQLA table methods in turn. The source code is well worth looking at for
this one.

## Example

Let's keep building our example. We have our databases, roles, and extra schemas. Let's define
our tables and columns via SQLA then refer to them via the `DatabaseContent` class:

```Python
{!./docs_src/guide/tables.py[ln:1-33]!}

# omitted code below
```

In the code above, we import `DatabaseContent` from `dbdeclare` and we import `DeclarativeBase`
from `sqlalchemy`. We then define a base and a bunch of tables. Please refer to
[SQLA documentation](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#orm-declarative-mapping) for more information on how to define tables and columns.
Now let's refer to the base:

```Python hl_lines="9 12"
# omitted code above

{!./docs_src/guide/tables.py[ln:36-37]!}

    # omitted code between

{!./docs_src/guide/tables.py[ln:48-52]!}

# omitted code below
```

We update the schema definition so that we store a reference to it in `log_schema`. We then
define our `DatabaseContent` and have it point to `db`, `ExampleBase`, and `log_schema` so that
Postgres will know exactly where to put these tables and what entities need to exist before these
tables can exist.

This code now defines the databases, roles, schemas, tables, and columns we need. Apart from
actually creating all this in the cluster, all we need to do is [grant privileges](/guide/grants).