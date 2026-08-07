"""Tests pour POST /api/register et POST /api/login."""


def test_register_success(client):
    response = client.post("/api/register", json={
        "email": "alice@test.com",
        "full_name": "Alice Dupont",
        "password": "motdepasse123",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@test.com"
    assert body["full_name"] == "Alice Dupont"
    assert "hashed_password" not in body  # jamais exposé au client (D-Model/Schema boundary)
    assert "password" not in body
    assert "access_token" not in body  # D1 : register ne connecte pas automatiquement
    assert body["created_at"] == body["updated_at"]  # D11


def test_register_missing_full_name_returns_422(client):
    """D2 : full_name est obligatoire à l'inscription."""
    response = client.post("/api/register", json={
        "email": "missingname@test.com",
        "password": "motdepasse123",
    })

    assert response.status_code == 422


def test_register_password_too_long_returns_422(client):
    """D13 : borne haute (72 caractères, limite bcrypt), pas seulement la borne basse."""
    response = client.post("/api/register", json={
        "email": "longpass@test.com",
        "full_name": "Long Pass",
        "password": "a" * 73,
    })

    assert response.status_code == 422


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "bob@test.com", "full_name": "Bob", "password": "motdepasse123"}
    client.post("/api/register", json=payload)

    response = client.post("/api/register", json=payload)

    assert response.status_code == 409


def test_register_invalid_email_returns_422(client):
    response = client.post("/api/register", json={
        "email": "pas-un-email",
        "full_name": "Bob",
        "password": "motdepasse123",
    })

    assert response.status_code == 422


def test_register_short_password_returns_422(client):
    response = client.post("/api/register", json={
        "email": "carla@test.com",
        "full_name": "Carla",
        "password": "abc",
    })

    assert response.status_code == 422


def test_register_whitespace_only_name_returns_422(client):
    response = client.post("/api/register", json={
        "email": "dan@test.com",
        "full_name": "   ",
        "password": "motdepasse123",
    })

    assert response.status_code == 422


def test_login_success_returns_valid_token(client):
    client.post("/api/register", json={
        "email": "eve@test.com",
        "full_name": "Eve",
        "password": "motdepasse123",
    })

    response = client.post("/api/login", json={
        "email": "eve@test.com",
        "password": "motdepasse123",
    })

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post("/api/register", json={
        "email": "frank@test.com",
        "full_name": "Frank",
        "password": "motdepasse123",
    })

    response = client.post("/api/login", json={
        "email": "frank@test.com",
        "password": "mauvais_mot_de_passe",
    })

    assert response.status_code == 401


def test_login_unknown_email_returns_401(client):
    response = client.post("/api/login", json={
        "email": "inconnu@test.com",
        "password": "nimportequoi",
    })

    assert response.status_code == 401


def test_login_anti_enumeration_identical_error_messages(client):
    """
    Décision D5 : le message d'erreur doit être STRICTEMENT identique,
    que l'email soit inconnu ou que le mot de passe soit incorrect -
    sinon un attaquant peut déduire quels emails existent en base.
    """
    client.post("/api/register", json={
        "email": "grace@test.com",
        "full_name": "Grace",
        "password": "motdepasse123",
    })

    wrong_password = client.post("/api/login", json={
        "email": "grace@test.com",
        "password": "mauvais",
    })
    unknown_email = client.post("/api/login", json={
        "email": "totalement_inconnu@test.com",
        "password": "mauvais",
    })

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_jwt_payload_contains_no_business_data(client):
    """
    Décision D17 : le JWT ne doit contenir QUE sub/type/iat/exp - jamais
    l'email ou le nom, pour éviter la duplication de données mutables
    dans un token non chiffré (lisible par n'importe qui, cf. jwt.io).
    """
    client.post("/api/register", json={
        "email": "henri@test.com",
        "full_name": "Henri Secret",
        "password": "motdepasse123",
    })
    response = client.post("/api/login", json={
        "email": "henri@test.com",
        "password": "motdepasse123",
    })
    token = response.json()["access_token"]

    from jose import jwt as jose_jwt
    from app.core.config import settings
    payload = jose_jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    assert set(payload.keys()) == {"sub", "type", "iat", "exp"}
    assert payload["type"] == "access"
    assert "email" not in payload
    assert "full_name" not in payload


def test_password_is_hashed_with_bcrypt(client):
    """D18 : le mot de passe est stocké hashé avec bcrypt (préfixe $2b$),
    jamais en clair - vérifié directement en base, pas via l'API."""
    client.post("/api/register", json={
        "email": "iris@test.com",
        "full_name": "Iris",
        "password": "motdepasse123",
    })

    from tests.conftest import TestingSessionLocal
    from app.modules.users.model import User

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "iris@test.com").first()
    db.close()

    assert user.hashed_password.startswith("$2b$")
    assert user.hashed_password != "motdepasse123"


def test_tampered_token_signature_returns_401(client):
    """
    Vérifie concrètement qu'une signature altérée est rejetée - pas
    juste une chaîne aléatoire (déjà testé ailleurs), mais un VRAI token
    valide dont un seul caractère de la signature a été modifié.
    """
    client.post("/api/register", json={
        "email": "jack@test.com",
        "full_name": "Jack",
        "password": "motdepasse123",
    })
    response = client.post("/api/login", json={
        "email": "jack@test.com",
        "password": "motdepasse123",
    })
    token = response.json()["access_token"]
    tampered = token[:-5] + "XXXXX"

    response = client.get("/api/profile", headers={"Authorization": f"Bearer {tampered}"})

    assert response.status_code == 401