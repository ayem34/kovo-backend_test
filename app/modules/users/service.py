from fastapi import HTTPException, status

from app.core.password import hash_password
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate


def register_user(data: UserCreate, repository: UserRepository) -> User:
    """
    Règle métier de l'inscription (décision D1 : ne connecte pas
    automatiquement l'utilisateur, pas de JWT renvoyé ici).
    """
    existing = repository.get_by_email(data.email)
    if existing is not None:
        # 409 Conflict : le client a envoyé une requête valide dans sa
        # forme, mais elle entre en conflit avec l'état actuel du serveur.
        # C'est plus précis qu'un 400 générique.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email.",
        )

    new_user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )

    return repository.create(new_user)
