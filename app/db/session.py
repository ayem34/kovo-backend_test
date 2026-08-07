from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dépendance FastAPI : ouvre une session DB au début d'une requête,
    la fournit au router via injection de dépendance, puis la ferme
    systématiquement à la fin (même si une exception survient).
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
