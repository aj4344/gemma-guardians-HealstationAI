"""Alembic environment: migrations run in-process from Database.migrate()."""

from alembic import context

from healstation.store.models import Base

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connection = context.config.attributes["connection"]
    # SQLite cannot ALTER most constraints in place; batch mode rebuilds tables.
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
