# Grants

First, we'll go over the details of how grants are implemented. Then, we'll continue to build our
example. You can also [skip ahead](#example) to the example.

## Grantable entities

The `Grantable` class is an internal class used by DbDeclare (aka you won't use it unless you are developing
and extending the package). It defines behavior for any entity that can have privileges granted to it. This
includes entities like databases, schemas, and tables. Grantable entities work in tandem with `Role`s to
define access privileges, like connecting to a database or selecting from a table. Ultimately, you are able
to define relationships that result in a `GRANT {privileges} ON {entity_type} {entity} TO {role}`.

### Privileges

Privileges are a set list of access control definitions, check out the [Postgres documentation](https://www.postgresql.org/docs/current/ddl-priv.html#PRIVILEGE-ABBREVS-TABLE)
for a complete overview. DbDeclare defines them all in a Python `enum`:

```Python
from dbdeclare.data_structures import Privilege
```

Use this to define what privileges you want to when you define a grant.

### Multiple ways to grant

Grantable entities and `Role`s can both define grants.

#### From a role

The `Role` class has a `grant` method that accepts a `Sequence[GrantOn]`, where `GrantOn` can be found
in `data_structures`:

```Python
from dbdeclare.data_structures import GrantOn
```

`GrantOn` is a dataclass that has two attributes: `privileges`, which is a `Sequence[Privilege]`, and
`on`, which is a sequence of `Grantable` entities to grant those privileges on.

You can also pass in a `Sequence[GrantOn]` when you define a `Role` via the `__init__` method, if it is
more convenient to do so.

#### From a grantable entity

Anything that inherits from `Grantable` also has a `grant` method, but this one accepts a `Sequence[GrantTo]`.
`GrantTo` can also be found in `data_structures`:

```Python
from dbdeclare.data_structures import GrantTo
```

`GrantTo` is a dataclass that has two attributes: `privileges`, which is a `Sequence[Privilege]`, and
`to`, which is a sequence of `Role`s to grant those privileges to.

You can also pass in a `Sequence[GrantTo]` when you define any grantable entity via the `__init__` method,
if it is more convenient to do so.

### How grants are stored

So what actually happens when you run the `grant` methods described above? We store them in the `Role` that 
access is granted to for easy synchronization. DbDeclare also makes sure that the order of creates and grants is
correct so that execution doesn't fail. Each `Role` has an attribute named `grants` of type `GrantStore`, which is
an alias for `dict[Grantable, set[Privilege]]`. This structure is easy to translate to and from Postgres, and makes
sure there is a single source of truth within the code.

As always, I encourage you to peek at the source code and read the docstrings for details!

## Example

Let's add grants to our example. We have defined all the entities we want to create, so now we can
run some `grant` statements.

```Python
{!./docs_src/guide/grants.py[ln:3]!}
```

For our example, I've opted to grant privileges from the point of view of `Role`s only, which means I
import `GrantOn` but not `GrantTo`.

```Python
# omitted code above

{!./docs_src/guide/grants.py[ln:56-79]!}

# omitted code below
```

Here, we grab our references for `etl_writer`, `ml_writer`, and `reader`, and define grants for each of them.
We allow `etl_writer` to insert and update on the `article` and `keyword` table, we allow `ml_writer`
to insert and update on the `cluster` table, and we allow `reader` to select from all three of those tables.
Note that we don't have to grant usage of the default schema as (typically) usage is granted to all users
by default. Depending on your set up, you _may_ need to grant connect on the roles to each database.

```Python
# omitted code above

{!./docs_src/guide/grants.py[ln:82-95]!}

# omitted code below
```

We also need to grant insert, select, and update privileges to `log_role` on both tables in the `log` schema.
Since this is a non-default schema, we first grant usage on the schema, then we grant the desired privileges
on both tables. Note that this is done in the creation of the role, in contrast to the previous examples that
call `grant` on the roles _after_ they were defined. Do whatever makes more sense for you.

Here is the entire file now:

```Python
{!./docs_src/guide/grants.py!}
```

We have defined everything we set out to define. Nice! All that's left is to actually create all
of this in the database. Let's [run it](/guide/controller)!