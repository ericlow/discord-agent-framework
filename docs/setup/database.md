# Setting up the database (Neon)

The agent stores conversations in Postgres so follow-up turns can reload history.
We use [Neon](https://neon.tech) — free-forever serverless Postgres
([ADR-002](../adr/ADR-002-database.md)).

## 1. Create a Neon project

1. Sign up (free, no card) at <https://neon.tech>.
2. Create a new project and pick a **region**.
3. Leave the Postgres version at the default.

**Match the region to your Lambda.** The database region and `aws_region` in
`infra/terraform.tfvars` should be the same, or every query hops across regions.
Set whichever you choose second to match the first — e.g. a Neon project in
`us-west-2` means `aws_region = "us-west-2"`.

Neon creates a default database for you — you can use it, or note the database name
for the connection string in the next step.

## 2. Copy the pooled connection string

On the project **Dashboard**, click **Connect** (or **Connection string**). A dialog
opens with the connection string; **connection pooling is enabled by default** in
recent Neon — confirm the hostname contains `-pooler`. Lambda opens many short-lived
connections, so the pooled endpoint avoids exhausting Postgres connection limits.

Neon may show the string prefixed for the `psql` command — copy only the URL itself
(the part inside the quotes). It looks like:

```
postgresql://user:password@ep-xxxx-pooler.us-west-2.aws.neon.tech/dbname?sslmode=require&channel_binding=require
```

This string **is a secret** (it contains the password). Save it in two gitignored
places — do not commit it:

- `infra/terraform.tfvars` → `database_url = "..."` (Terraform sets the Lambda env)
- `.env` at the repo root → `DATABASE_URL=...` (for the local `db/init_db.py` step)

## 3. Create the `conversations` table

With `DATABASE_URL` in `.env`, run the init script once from the repo root (inside
your virtualenv):

```bash
python db/init_db.py
```

Expected output:

```
Database already exists: neondb
Schema applied.
```

Neon already provides the database, so the script skips creation and just applies
`db/schema.sql` (the `conversations` table). It's idempotent — safe to re-run.

