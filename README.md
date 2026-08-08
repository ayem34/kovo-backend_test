# Kôvo Backend — Test technique

API REST d'authentification et de gestion de profil, développée dans le cadre d'un test
technique pour un poste de développeur backend. Construite avec **FastAPI**, **PostgreSQL**
et **JWT**, en suivant les principes SOLID, Clean Code, et une architecture en couches.

## 🔗 Liens

| | |
|---|---|
| **API déployée** | https://kovo-backend-test.onrender.com |
| **Documentation interactive (Swagger)** | https://kovo-backend-test.onrender.com/docs |
| **Dépôt Git** | https://github.com/ayem34/kovo-backend_test |
| **Journal des décisions d'architecture** | [DECISIONS.md](./DECISIONS.md) |

## Sommaire

- [Endpoints](#endpoints)
- [Stack technique](#stack-technique)
- [Installation locale](#installation-locale)
- [Variables d'environnement](#variables-denvironnement)
- [Tests](#tests)
- [Sécurité](#sécurité)
- [Limitations connues](#limitations-connues)
- [Structure du projet](#structure-du-projet)

## Endpoints

| Méthode | Route | Description | Protégé |
|---|---|---|---|
| `POST` | `/api/register` | Créer un compte | Non |
| `POST` | `/api/login` | S'authentifier, obtenir un JWT | Non |
| `GET` | `/api/profile` | Consulter son propre profil | Oui (JWT) |
| `PUT` | `/api/profile` | Modifier son nom complet | Oui (JWT) |
| `GET` | `/` | Health check | Non |

Documentation complète des schémas de requête/réponse : voir `/docs` (Swagger, généré
automatiquement).

## Stack technique

- **FastAPI** — framework web, choisi pour sa validation native (Pydantic), sa documentation
  OpenAPI générée automatiquement, et son typage strict (justification comparative détaillée
  dans `DECISIONS.md`, décision D19)
- **SQLAlchemy 2.0** — ORM, syntaxe typée moderne (`Mapped`, `mapped_column`)
- **PostgreSQL** — base relationnelle, via **psycopg3**
- **Alembic** — migrations de schéma versionnées
- **JWT** (`python-jose`) — authentification stateless, payload minimal
- **bcrypt** (`passlib`) — hash des mots de passe
- **pytest** — tests automatisés (23 tests)
- **Docker / docker-compose** — conteneurisation

Chaque choix technique est justifié individuellement dans **[DECISIONS.md](./DECISIONS.md)**
(21 décisions tracées, D1 à D21).

## Architecture

Organisation **par module métier** plutôt que par couche technique :

```
app/
├── main.py                 # Point d'entrée FastAPI
├── core/                   # Infrastructure transverse
│   ├── config.py           # Configuration (variables d'environnement)
│   ├── jwt.py               # Création/vérification des tokens
│   ├── password.py         # Hash/vérification bcrypt
│   └── dependencies.py     # Dépendance d'authentification (get_current_user)
├── db/                     # Connexion base de données
│   ├── base.py
│   └── session.py
└── modules/
    └── users/               # Domaine métier "users"
        ├── model.py         # Modèle SQLAlchemy
        ├── schema.py         # Schémas Pydantic (validation)
        ├── repository.py    # Accès aux données (CRUD pur)
        ├── service.py       # Logique métier
        └── router.py         # Endpoints HTTP
```

Chaque couche a une responsabilité unique : le router valide et délègue, le service applique
les règles métier, le repository ne fait que du CRUD sans aucune logique métier (voir D8).

## Installation locale

### Option A — Docker (recommandée)

```bash
git clone https://github.com/ayem34/kovo-backend_test.git
cd kovo-backend_test
cp .env.example .env
# Éditer .env : remplacer SECRET_KEY par une vraie valeur aléatoire
docker-compose up --build
```

L'API est disponible sur http://localhost:8000/docs — PostgreSQL et l'application démarrent
ensemble, migrations incluses automatiquement.

### Option B — Environnement Python local

Prérequis : Python 3.12 (les versions plus récentes peuvent poser des problèmes de
compatibilité avec certaines dépendances, voir D12).

```bash
git clone https://github.com/ayem34/kovo-backend_test.git
cd kovo-backend_test
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec les identifiants d'une base PostgreSQL locale
alembic upgrade head
uvicorn app.main:app --reload
```

## Variables d'environnement

| Variable | Description |
|---|---|
| `DATABASE_URL` | URL de connexion PostgreSQL (format `postgresql+psycopg://...`) |
| `SECRET_KEY` | Clé de signature des JWT — doit être une valeur aléatoire robuste en production |
| `ALGORITHM` | Algorithme de signature JWT (défaut : `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de vie d'un token, en minutes (défaut : `60`) |

Avec `docker-compose`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` configurent en
plus le conteneur PostgreSQL lui-même. Voir `.env.example` pour un modèle complet.

## Tests

```bash
pytest tests/ -v
```

23 tests couvrant : validation des entrées, unicité des emails, hash des mots de passe,
anti-énumération sur le login, contenu minimal du JWT, protection anti-IDOR sur le profil,
comportement de `updated_at`, et rejet des tentatives de modification de champs non autorisés
(email, mot de passe via `PUT /profile`).

## Sécurité

- Mots de passe hashés avec **bcrypt** (jamais stockés en clair)
- JWT au payload minimal (`sub`, `type`, `iat`, `exp` uniquement — aucune donnée métier)
- **Anti-énumération** sur `/login` : message d'erreur strictement identique, que l'email
  soit inconnu ou le mot de passe incorrect
- **Anti-IDOR** sur `/profile` : aucun ID utilisateur accepté dans l'URL ou le body, la
  cible est déduite exclusivement du JWT
- Gestionnaire d'erreurs global : aucune trace Python (stack trace) exposée au client en
  cas d'erreur interne imprévue
- Secrets exclusivement via variables d'environnement, jamais commités

## Limitations connues

Choix assumés et documentés (voir `DECISIONS.md` pour le détail) :

- **Changement de mot de passe** non disponible via `PUT /profile` — nécessiterait un
  endpoint dédié avec re-saisie du mot de passe actuel (D3)
- **Timing attacks** sur `/login` non traités — une protection complète nécessiterait un
  appel factice à bcrypt même quand l'utilisateur n'existe pas (D14)

## Structure du projet

```
kovo-backend/
├── app/                     # Code applicatif
├── alembic/                 # Migrations de base de données
├── tests/                   # Suite de tests automatisés
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── DECISIONS.md             # Journal des décisions d'architecture
└── README.md
```
