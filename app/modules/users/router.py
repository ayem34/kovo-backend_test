from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserLogin, UserOut, UserUpdate, Token
from app.modules.users import service

router = APIRouter(prefix="/api", tags=["users"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    Le router ne contient aucune règle métier : il valide la forme (via
    UserCreate, automatique), délègue au service, et sérialise la réponse
    (via response_model=UserOut, qui garantit qu'aucun champ imprévu -
    comme hashed_password - ne peut fuiter dans la réponse HTTP).
    """
    repository = UserRepository(db)
    return service.register_user(data, repository)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Vérifie les identifiants et renvoie un JWT (décision D1 : register
    ne connecte pas automatiquement, cette route est le seul moyen
    d'obtenir un token)."""
    repository = UserRepository(db)
    access_token = service.login_user(data, repository)
    return Token(access_token=access_token)


@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """
    Décision D6 : aucun ID dans l'URL. L'utilisateur retourné est
    exclusivement celui identifié par le token JWT (via get_current_user),
    jamais un profil choisi par le client - élimine par construction
    toute faille IDOR sur cette route.
    """
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Même garantie que GET /profile : seul le propriétaire du token peut
    modifier son propre profil, et uniquement full_name (D3/D4)."""
    repository = UserRepository(db)
    return service.update_profile(current_user, data, repository)
