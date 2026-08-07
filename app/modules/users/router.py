from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserOut
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
