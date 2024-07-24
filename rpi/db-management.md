# DB management

## Generate DB schema from all migrations (development)

```bash
$ cd core
$ alembic upgrade head --sql > db_schema.sql
```

## Generate SQL from migration(s) (development)

```bash
$ cd core
$ alembic upgrade start:end --sql > migration.sql
```

Where `start` and `end` are the _revision identifiers_ used by Alembic to identify each version.

## Execute a SQL script

```bash
$ docker exec -i remote-cnc-postgresql psql -U {{DB_USER}} --dbname={{DB_NAME}} < /path/to/script.sql
```

## Backup DB

```bash
$ docker exec -i remote-cnc-postgresql pg_dump -U {{DB_USER}} {{DB_NAME}} > /path/to/db_schema.sql
```
