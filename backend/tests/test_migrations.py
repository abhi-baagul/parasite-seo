from sqlalchemy import inspect

from app.db.base import Base
from app.db.session import engine
from app.models import load_models
from tests.test_health import REQUIRED_TABLES


def test_all_models_registered() -> None:
    load_models()
    assert REQUIRED_TABLES.issubset(set(Base.metadata.tables))


def test_migration_created_all_tables() -> None:
    load_models()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = REQUIRED_TABLES - tables
    assert not missing, f"Missing tables: {missing}"
    assert "alembic_version" in tables
