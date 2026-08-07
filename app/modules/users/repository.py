import uuid

from sqlalchemy.orm import Session

from app.modules.users.model import User


class UserRepository:
    """
    Accès aux données de la table `users`, et RIEN d'autre.
    Aucune règle métier ici (cf. décision D8) : pas de vérification
    d'unicité, pas de hash de mot de passe. Juste du CRUD.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)  # recharge les valeurs générées par la DB
        return user            # (id, created_at, updated_at via server_default)

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user
