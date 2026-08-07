import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.config import settings

# Base de test dédiée : même serveur PostgreSQL que le développement,
# mais une base séparée pour ne jamais polluer les données réelles ni
# dépendre de leur état entre deux exécutions de la suite de tests.
TEST_DATABASE_URL = settings.database_url.replace("/kovo_db", "/kovo_db_test")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Remplace la dépendance get_db de l'app par une session pointant
    vers la base de test, sans toucher au code applicatif lui-même."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """
    Recrée les tables avant CHAQUE test, et les supprime après.
    autouse=True : appliqué automatiquement à tous les tests sans avoir
    à le déclarer explicitement dans chacun. Garantit un état propre et
    isolé pour chaque test, indépendamment de l'ordre d'exécution.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Client de test HTTP, prêt à appeler l'API comme le ferait un vrai client."""
    return TestClient(app)
