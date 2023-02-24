# Controller

First, we'll go over the basics and examine the `Controller` class. Then, we'll finish up our example.

## The Controller class

You can import the `Controller` like so:

```Python
from dbdeclare.controller import Controller
```

The `Controller` executes commands in the cluster. It looks at everything you've declared and (depending on
the function you call) creates/drops entities and grants/revokes privileges. Under the hood, it iterates
over all entities and executes their specific commands. So if all you have declared is something like:

```Python
db = Database(name="dev")
```

The only SQL executed from `Controller.run_all` will be:

```sql
CREATE DATABASE dev;
```

There are a handful of functions to choose from. `run_all` and `remove_all` are the most likely entrypoints.
`run_all` runs `create_all` which creates all declared entities, then runs `grant_all` which grants all declared
privileges. `remove_all` runs `revoke_all` which revokes all privileges, then runs `drop_all` which drops all
declared entities.  Take a look at the class docstrings for more detail. The `Controller` interacts heavily with
the underlying `Entity` class and is to some extent a wrapper around it.

For what it's worth, this is where a lot of future development will go: we'd like to eventually have updates,
change detection, integration with Alembic, and more.

## Example

Let's finish up our example. We have all our entities declared, and we have all our grants declared as well.
Now we just need to execute:

```Python hl_lines="1 4 9 11"
{!./docs_src/guide/controller.py[ln:1-4]!}

# omitted code between

{!./docs_src/guide/controller.py[ln:104-107]!}

```

We import `create_engine` from SQLA and `Controller` from DbDeclare. We create an engine, and make sure
to provide a user with admin privileges (you might need to adjust your cluster url relative to the example).
Pass the engine to the `run_all` method, and we're done! It'll create all the entities and grant all privileges.

The entire, complete file:

```Python
{!./docs_src/guide/controller.py!}
```

If you run this (with an active Postgres instance/cluster), it should create all the databases, roles, schemas,
and tables. It should also grant all the privileges declared. You can test via psql:

```shell
> psql -h 127.0.0.1 -U dev_api -d dev

dev=> SELECT * FROM log.good_request;
 id 
----
(0 rows)
```

There's nothing in there, but the database, schema, role, and access privileges are all present! Woo!

That's all for now. The future holds more features, and this documentation will be updated as they're added.