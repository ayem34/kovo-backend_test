import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.core.config import settings


def create_access_token(user_id: uuid.UUID) -> str:
    """
    Génère un JWT signé pour l'utilisateur donné.

    Le payload reste volontairement minimal (sub, type, iat, exp) : aucune
    donnée métier (email, nom...) n'y est stockée, car un JWT n'est PAS
    chiffré, seulement signé — son contenu est lisible par n'importe qui
    (cf. jwt.io). Toute donnée sensible ou mutable n'a rien à y faire.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),  # "subject" : à qui appartient ce token
        "type": "access",     # distingue d'un futur éventuel refresh token
        "iat": now,           # issued at
        "exp": expire,        # expiration : obligatoire, jamais de token éternel
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> uuid.UUID | None:
    """
    Vérifie la signature et l'expiration du token, puis retourne l'ID
    utilisateur qu'il contient.

    Retourne None si le token est invalide, altéré, expiré, ou n'est pas
    un access token (protection contre un futur refresh token mal utilisé
    ici). On ne lève pas d'exception ici : c'est la dépendance FastAPI qui
    appelle cette fonction (étape suivante) qui décide de la réponse HTTP
    appropriée (401), pas cette fonction utilitaire.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    subject = payload.get("sub")
    if subject is None:
        return None

    try:
        return uuid.UUID(subject)
    except ValueError:
        return None
