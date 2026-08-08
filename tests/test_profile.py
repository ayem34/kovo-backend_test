"""Tests pour GET /api/profile et PUT /api/profile."""

import pytest


@pytest.fixture
def auth_headers(client):
    """
    Fixture composée : crée un utilisateur, se connecte, et retourne les
    headers Authorization prêts à l'emploi. Réutilisée par tous les tests
    de ce fichier qui ont besoin d'un utilisateur authentifié - évite de
    répéter register+login dans chaque test.
    """
    client.post("/api/register", json={
        "email": "profile_user@test.com",
        "full_name": "Profile User",
        "password": "motdepasse123",
    })
    response = client.post("/api/login", json={
        "email": "profile_user@test.com",
        "password": "motdepasse123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_profile_without_token_returns_401(client):
    response = client.get("/api/profile")

    assert response.status_code == 401


def test_get_profile_with_invalid_token_returns_401(client):
    response = client.get("/api/profile", headers={"Authorization": "Bearer invalide"})

    assert response.status_code == 401


def test_get_profile_success(client, auth_headers):
    response = client.get("/api/profile", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "profile_user@test.com"
    assert body["full_name"] == "Profile User"
    assert "hashed_password" not in body


def test_put_profile_updates_full_name(client, auth_headers):
    response = client.put("/api/profile", headers=auth_headers, json={
        "full_name": "Nom Modifié",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Nom Modifié"


def test_put_profile_updates_updated_at_timestamp(client, auth_headers):
    before = client.get("/api/profile", headers=auth_headers).json()

    after_response = client.put("/api/profile", headers=auth_headers, json={
        "full_name": "Autre Nom",
    })
    after = after_response.json()

    assert after["created_at"] == before["created_at"]  # jamais modifié
    assert after["updated_at"] != before["updated_at"]  # a changé (D11, onupdate)


def test_put_profile_ignores_email_field(client, auth_headers):
    """
    Décision D4 : l'email n'est pas modifiable via cette route, même si
    le client tente de l'injecter dans le body - UserUpdate ne déclare
    pas ce champ, donc Pydantic l'ignore silencieusement.
    """
    response = client.put("/api/profile", headers=auth_headers, json={
        "full_name": "Test",
        "email": "hacker@evil.com",
    })

    assert response.status_code == 200
    assert response.json()["email"] == "profile_user@test.com"


def test_put_profile_ignores_password_field(client, auth_headers):
    """
    Décision D3 : le mot de passe n'est pas modifiable via cette route.
    On vérifie que l'ancien mot de passe fonctionne toujours au login
    après une tentative d'injection de 'password' dans le body du PUT.
    """
    client.put("/api/profile", headers=auth_headers, json={
        "full_name": "Test",
        "password": "nouveaumdp999",
    })

    response = client.post("/api/login", json={
        "email": "profile_user@test.com",
        "password": "motdepasse123",  # l'ancien mot de passe, toujours valide
    })

    assert response.status_code == 200


def test_put_profile_rejects_whitespace_only_name(client, auth_headers):
    response = client.put("/api/profile", headers=auth_headers, json={
        "full_name": "   ",
    })

    assert response.status_code == 422


def test_profile_cannot_be_accessed_with_another_users_token(client):
    """
    Décision D6 : chaque token ne donne accès qu'au profil de son
    propriétaire - vérifié ici avec deux utilisateurs distincts.
    """
    client.post("/api/register", json={
        "email": "user_a@test.com", "full_name": "User A", "password": "motdepasse123",
    })
    client.post("/api/register", json={
        "email": "user_b@test.com", "full_name": "User B", "password": "motdepasse123",
    })

    token_a = client.post("/api/login", json={
        "email": "user_a@test.com", "password": "motdepasse123",
    }).json()["access_token"]

    response = client.get("/api/profile", headers={"Authorization": f"Bearer {token_a}"})

    assert response.json()["email"] == "user_a@test.com"
    assert response.json()["email"] != "user_b@test.com"
