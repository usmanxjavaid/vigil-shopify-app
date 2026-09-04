import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from config import settings
from persistence.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Single source of truth — pull the real DB URL from our own config.py
# instead of duplicating credentials inside alembic.ini as plain text.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Points autogenerate at our actual table definitions, so it can compare
# what's in models.py against what's really in the database.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Same PgBouncer-safety settings as db.py, applied here too — migrations
    # go through Neon's pooler exactly like normal app traffic does.
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"ssl": "require", "statement_cache_size": 0},
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()