# Roles

First, we'll go over basics and examine the `Role` class. Then, we'll continue to build our example.
You can also [skip ahead](#example) to the example.

## The Role class

You can import `Role` like so:

```Python
from dbdeclare.entities import Role
```

`Role` is a representation of a [Postgres role](https://www.postgresql.org/docs/current/database-roles.html).
It is a cluster-wide entity. This means each role in your cluster must have a unique name. The `__init__` args
correspond to the SQL `CREATE ROLE` arguments found in the [Postgres documentation](https://www.postgresql.org/docs/current/sql-createrole.html).

Take a look at the class docstrings for more detail, like an explanation of the `__init__` args, the various methods
defined, what classes it inherits from, and more. `Role` is unique amongst the entities because you can only grant
privileges _to_ a role. We'll go into more detail when we discuss grants, but roles store the defined grants and call
all the granted target entity `grant` methods to actually execute grants. Point being, `Role` is unique and it
is worth taking a look at the source code.

## Example

Let's keep building our example. We have our databases, now we need our roles. We have a lot: some that act
like groups (roles that don't log in and typically have access privileges granted to them) and some that are
users (roles that can log in). We don't need to change our `main` function, just the `define_stage` one:

```Python
{!./docs_src/guide/roles.py[ln:1-19]!}
```

1. We're keeping the function header and `Database` definition from before.

Okay, we added a bunch of lines. Let's zoom in and break down what they're doing.

```Python hl_lines="4-6"
# omitted code above

{!./docs_src/guide/roles.py[ln:7-19]!}

# omitted code below
```
The highlighted lines create the etl_writer, ml_writer, and reader groups we want. We have not implemented
the access privileges yet; that'll come later. We make sure to prepend the names with the `stage` input so
that they are unique across the cluster, but clearly defined for each stage we want. For example, we'll have a
`test_reader`, `dev_reader`, and `prod_reader` as a result of running this for all three stages. The default
argument for `login` is `False`, so these roles cannot log in and have no password associated with them.

```Python hl_lines="9-10"
# omitted code above

{!./docs_src/guide/roles.py[ln:7-19]!}

# omitted code below
```

The highlighted lines create the etl and ml users we want. We make sure to specify `login=True` and provide
a (dummy) password. We also specify what groups they are _in_. For example, the `dev_etl` user is defined
to be _in_ the `dev_etl_writer` and `dev_reader` roles, where it will attain all the privileges granted to
them (once we grant privileges later). We don't assign the output to a variable because we aren't referring
to these roles later.

```Python hl_lines="13-15"
# omitted code above

{!./docs_src/guide/roles.py[ln:7-19]!}

# omitted code below
```

The last lines highlighted here create a group and a user for any stage that isn't the test stage. Otherwise,
you've now seen this all before! So there will be a `dev_logger` and a `prod_logger`, but no `test_logger`.

You can then run the entire file (which won't make anything happen) just to see that it doesn't error out:

```Python
{!./docs_src/guide/roles.py!}
```

1. We're keeping the function header and `Database` definition from before.
2. We're keeping the `main` function the same as well.

This defines what was already defined and now defines all the roles. Great! Our example needs a non-default
schema next. Let's [add a schema](/guide/schemas).