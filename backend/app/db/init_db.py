"""Optional metadata bootstrap. Schema changes must go through Alembic."""

from app.db.base import Base
from app.db.session import engine
from app.models import load_models


def init_db() -> None:
    load_models()
    Base.metadata.create_all(bind=engine)
