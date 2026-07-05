from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings
from app.core.security import hash_password


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models.user import User

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User).where(User.username == settings.default_admin_username)
        )
        if existing_admin is not None:
            return

        admin = User(
            username=settings.default_admin_username,
            display_name=settings.default_admin_display_name,
            password_hash=hash_password(settings.default_admin_password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
