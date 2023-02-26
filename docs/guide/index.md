# User guide

This guide will use one main over-arching example as a way to walk through everything DbDeclare can do. Some details
are omitted as they are unnecessary for the example, and some are contrived to show more functionality.

## The example

Let's say we have an application that takes in articles from a variety of news sites, clusters them, and exposes
the clusters via an API. We also want to store API logs (yes, this is typically not done in tables in Postgres, please
bear with me for the sake of the example). We want to accommodate 3 stages in our cluster: `test`, `dev`, and `prod`
(yes, it is typically best practice to have prod in a completely separate cluster/instance, but
humor me for this example). So for each stage, we want the following:

- Schemas and tables:
    - In the `default` schema, tables for: `Article`, `Keyword`, `Cluster`
    - In a `log` schema, tables for: `BadRequest`, `GoodRequest`
- Groups (roles that will not log in but define privileges):
    - An `etl_writer` role that can insert and update on `Article` and `Keyword`
    - A `ml_writer` role that can insert and update on `Cluster`
    - A `reader` role that can select on `Article`, `Keyword`, and `Cluster`
    - A `log` role that can insert, update, and select on `BadRequest` and `GoodRequest` (omit for `test`)
- Users (roles that will log in):
    - An `etl` role that is a member of `etl_writer` and `reader`
    - An `ml` role that is a member of `ml_writer` and `reader`
    - An `api` role that is a member of `log` and `reader` (omit for `test`)

Sound like a lot? No worries, we'll take it step by step. [Let's start with our databases](/guide/databases).
If this seems straightforward, and you'd prefer to just see the entire example, [skip ahead](/guide/controller).