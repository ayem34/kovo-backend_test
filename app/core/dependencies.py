from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.jwt import decode_access_token
from app.db.session import get_db
from app.modules.users.model import User
from app.modules.users.repository import UserRepository

# auto_error=True (par défaut) : si le header Authorization est absent,
# FastAPI renvoie automatiquement 403 avant même d'exécuter cette fonction.
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dépendance réutilisable pour toute route protégée : extrait le JWT du
    header Authorization, le valide, et retourne l'utilisateur correspondant.
    Centralise la logique d'authentification (DRY) plutôt que de la
    dupliquer dans chaque route protégée (GET/PUT /profile aujourd'hui,
    d'éventuelles futures routes protégées demain).
    """
    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repository = UserRepository(db)
    user = repository.get_by_id(user_id)

    if user is None:
        # L'utilisateur a été supprimé après l'émission du token : le
        # token est signé valide, mais ne correspond plus à personne.
        # 401 (pas 404) car c'est un problème d'authentification, pas
        # une route mal formée.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
