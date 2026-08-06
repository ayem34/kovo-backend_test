import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """Données attendues en entrée de POST /api/register."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    # max_length=72 : bcrypt tronque silencieusement au-delà de 72 octets,
    # on préfère rejeter explicitement plutôt que laisser un mot de passe
    # partiellement ignoré sans que l'utilisateur le sache.
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    """Données attendues en entrée de POST /api/login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)
    # Pas de min_length=8 ici volontairement : à la connexion, on ne valide
    # pas la robustesse du mot de passe, on vérifie juste sa correspondance
    # avec le hash stocké. Un mot de passe existant plus court que 8
    # caractères (créé avant un futur changement de règle, par exemple)
    # doit quand même pouvoir se connecter.


class UserUpdate(BaseModel):
    """
    Données attendues en entrée de PUT /api/profile.
    Volontairement limité à full_name (décisions D3 et D4) : ni l'email
    ni le mot de passe ne sont modifiables via cette route.
    """

    full_name: str = Field(min_length=1, max_length=255)


class UserOut(BaseModel):
    """
    Représentation d'un utilisateur renvoyée par l'API.
    Ne contient JAMAIS hashed_password : c'est le filtre volontaire entre
    le Model (SQLAlchemy, ce qui est stocké) et ce qui est exposé au client.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    created_at: datetime
    updated_at: datetime
