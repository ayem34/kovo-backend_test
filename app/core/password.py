from passlib.context import CryptContext

# bcrypt : algorithme volontairement lent, résistant à la force brute,
# avec un salt intégré automatiquement à chaque hash (cf. étape 9).
# deprecated="auto" : si on ajoute un jour un autre algorithme dans schemes,
# passlib pourra migrer progressivement les anciens hashs sans code
# supplémentaire à écrire.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash un mot de passe en clair. Utilisé uniquement à l'inscription."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare un mot de passe en clair à un hash stocké en base.
    Utilisé uniquement à la connexion. Ne révèle jamais si l'échec vient
    d'un email inconnu ou d'un mot de passe incorrect : c'est à l'appelant
    (le service, étape 11) de renvoyer un message générique dans les deux
    cas, pour éviter l'énumération de comptes (décision D5).
    """
    return pwd_context.verify(plain_password, hashed_password)
