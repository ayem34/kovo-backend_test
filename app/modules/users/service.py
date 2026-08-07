from fastapi import HTTPException, status

from app.core.jwt import create_access_token
from app.core.password import hash_password, verify_password
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserLogin


def register_user(data: UserCreate, repository: UserRepository) -> User:
    """
    Règle métier de l'inscription (décision D1 : ne connecte pas
    automatiquement l'utilisateur, pas de JWT renvoyé ici).
    """
    existing = repository.get_by_email(data.email)
    if existing is not None:
        # 409 Conflict : le client a envoyé une requête valide dans sa
        # forme, mais elle entre en conflit avec l'état actuel du serveur.
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


def login_user(data: UserLogin, repository: UserRepository) -> str:
    """
    Règle métier de la connexion : vérifie les identifiants et renvoie un
    JWT signé. Anti-énumération (décision D5) : que l'email n'existe pas
    OU que le mot de passe soit incorrect, on lève exactement la même
    exception, avec le même message générique.
    """
    user = repository.get_by_email(data.email)

    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    return create_access_token(user.id)
