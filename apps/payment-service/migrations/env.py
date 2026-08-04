import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add catalog-service app root and packages/python to Python path
# to guarantee imports resolve correctly in all environments.
migrations_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(migrations_dir, "..")))
sys.path.insert(0, os.path.abspath(os.path.join(migrations_dir, "..", "..", "..", "packages", "python")))

from app.core.config import settings
from showbook_common.models.base import Base
# Import models to register metadata for Alembic autogenerate
from app.models.payment import PaymentTransaction
from app.models.refund import Refund

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override the database URL dynamically
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.get_secret_value())

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in ("payment_transactions", "refunds", "alembic_version_payment")
    return True

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_payment",
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version_payment",
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
