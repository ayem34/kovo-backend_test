import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """
    Modèle SQLAlchemy représentant la table `users` en base de données.

    Ce modèle ne contient AUCUNE logique métier (pas de validation, pas de
    vérification d'unicité, pas de hash de mot de passe) : c'est le rôle du
    Service. Ici, uniquement la structure de la table.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        # Ne JAMAIS inclure hashed_password ici : __repr__ finit souvent
        # dans des logs, et on ne veut jamais qu'un hash de mot de passe
        # (même hashé) se retrouve dans un fichier de log.
        return f"<User id={self.id} email={self.email}>"
