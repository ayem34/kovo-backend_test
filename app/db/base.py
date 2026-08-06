from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Classe de base dont hériteront tous les modèles SQLAlchemy (User, et
    d'éventuels futurs modèles). Elle centralise les métadonnées de toutes
    les tables, ce qui est nécessaire pour qu'Alembic puisse détecter le
    schéma complet lors de la génération des migrations.
    """

    pass
