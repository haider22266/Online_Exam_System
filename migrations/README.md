Run `flask db init` from the project root to generate the Alembic migration environment, then use:

```powershell
flask db migrate -m "initial schema"
flask db upgrade
```

The generated migration files are environment-specific and should be committed after the first successful database migration.
