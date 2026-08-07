# DECISIONS.md — Journal des décisions d'architecture

Ce document trace les choix techniques et fonctionnels effectués pendant le développement,
avec leur justification. Objectif : que n'importe quel relecteur comprenne le "pourquoi"
derrière chaque décision, pas seulement le "quoi".

| ID | Sujet |
|----|------------------------------|
| D1 | Register sans auto-login |
| D2 | full_name obligatoire |
| D3 | Password non modifiable via PUT /profile |
| D4 | Email non modifiable via PUT /profile |
| D5 | Anti-énumération |
| D6 | Profile Ownership (anti-IDOR) |
| D7 | Architecture feature-based |
| D8 | Repository pattern |
| D9 | Pas d'exceptions custom (YAGNI) |
| D10 | Colonne updated_at |
| D11 | Stratégie updated_at |
| D12 | psycopg3 |
| D13 | Politique de mot de passe |
| D14 | Timing attacks (hors scope) |
| D15 | UUID |
| D16 | SQLAlchemy 2.0 |
| D17 | JWT minimal |
| D18 | bcrypt |
| D19 | FastAPI |

---

## D1 — Register ne connecte pas automatiquement l'utilisateur
**Décision** : `POST /api/register` crée le compte et renvoie les infos publiques du user (201),
sans JWT. L'utilisateur doit ensuite appeler `POST /api/login`.
**Justification** : séparation claire des responsabilités entre "créer un compte" et
"s'authentifier". Évite de mélanger deux logiques métier dans un seul endpoint.

## D2 — `full_name` est un champ obligatoire à l'inscription
**Décision** : le modèle `User` exige `email`, `password`, `full_name`.
**Justification** : demandé explicitement dans le scope du test ; un profil doit être
exploitable dès sa création.

## D3 — Le mot de passe n'est pas modifiable via `PUT /api/profile`
**Décision** : cette route ne permet de modifier que `full_name`.
**Justification** : changer un mot de passe implique des règles de sécurité différentes
(ex: re-saisie du mot de passe actuel, invalidation des sessions existantes). Mélanger
ça dans une route générique de mise à jour de profil est une mauvaise pratique. Cette
fonctionnalité pourra être introduite ultérieurement via un endpoint dédié
(`PUT /api/profile/password`), mais reste hors du scope strict demandé ici.

## D4 — L'email n'est pas modifiable via `PUT /api/profile`
**Décision** : l'email est en lecture seule après l'inscription.
**Justification** : le rendre modifiable impliquerait la nécessité de revalider l'unicité
et de gérer les conflits de mise à jour, potentiellement une re-validation du format, et
dans un vrai produit une confirmation par email. Complexité disproportionnée par rapport
au scope du test. Choix assumé et documenté plutôt que bricolé.

## D5 — Anti-énumération sur `/login`
**Décision** : que l'email n'existe pas OU que le mot de passe soit incorrect, la réponse
sera strictement identique (message générique + code 401).
**Justification** : empêche un attaquant de déduire quels emails sont enregistrés en base
en observant des messages d'erreur différents.

## D6 — `GET/PUT /api/profile` ciblent uniquement le propriétaire du token
**Décision** : aucun ID utilisateur n'est accepté dans l'URL ou le body de ces routes.
L'utilisateur cible est déduit exclusivement du JWT fourni.
**Justification** : élimine par construction toute faille de type IDOR (Insecure Direct
Object Reference) — impossible d'accéder ou modifier le profil d'un tiers.

## D7 — Architecture par module (feature-based) plutôt que par couche
**Décision** : le code métier est organisé sous `app/modules/<domaine>/` (ex: `users/`),
chaque module regroupant son `router.py`, `service.py`, `repository.py`, `model.py`,
`schema.py`. L'infrastructure transverse (`core/`, `db/`) reste séparée, en dehors des modules.
**Justification** : pour comprendre une fonctionnalité, un développeur ouvre un seul dossier
au lieu de naviguer entre plusieurs dossiers techniques. Ce pattern facilite l'évolution du
projet lorsque de nouveaux domaines métier sont ajoutés (ex: `products/`, `orders/`).

## D8 — Le repository ne contient aucune logique métier
**Décision** : `UserRepository` expose exclusivement des opérations CRUD pures
(`get_by_email`, `create`, `update`) sans aucune condition métier.
**Justification** : garder le repository "pur" permet de tester la logique métier (dans le
service) indépendamment de la base de données, et de remplacer l'implémentation de
persistance sans impacter le reste de l'application (principe d'inversion de dépendance).

## D9 — Pas de hiérarchie d'exceptions custom pour l'instant
**Décision** : utilisation de `HTTPException` (FastAPI) et des erreurs de validation
natives de Pydantic, sans `exceptions.py` dédié.
**Justification** : principe YAGNI — introduire une hiérarchie d'exceptions métier avant
d'en avoir un besoin concret serait de la sur-ingénierie pour ce scope.

## D10 — Colonne `updated_at` ajoutée bien que non strictement demandée
**Décision** : la table `users` inclut `updated_at`, en plus des colonnes strictement
exigées par le sujet (`id`, `email`, `full_name`, `hashed_password`).
**Justification** : le sujet ne demande pas explicitement de tracer les modifications, mais
`PUT /api/profile` modifie réellement des données. Coût d'implémentation nul, pratique standard,
et directement justifiable si questionné — donc conservée en connaissance de cause plutôt
qu'ajoutée par réflexe non questionné.

## D11 — `updated_at` initialisée à `created_at` plutôt que `NULL`
**Décision** : `updated_at` est `NOT NULL`, avec `server_default=func.now()` ET
`onupdate=func.now()`. À la création, `created_at == updated_at`. Ce n'est qu'après une
première modification que les deux valeurs divergent.
**Justification** : ce choix évite la propagation d'un type optionnel dans les modèles, les
schémas et les tests, tout en restant cohérent avec les conventions des principaux ORM.

## D12 — Driver PostgreSQL : psycopg3 plutôt que psycopg2
**Décision** : le projet utilise `psycopg[binary]` (psycopg3) au lieu de `psycopg2-binary`,
initialement prévu dans le choix de stack.
**Justification** : psycopg3 est la version officiellement recommandée pour les nouveaux
projets SQLAlchemy 2.0. Ce choix améliore la compatibilité avec les plateformes modernes et
remplace psycopg2, aujourd'hui en mode maintenance uniquement.

## D13 — Pas de règle de complexité forcée sur le mot de passe
**Décision** : le mot de passe est contraint uniquement en longueur (8 à 72 caractères),
sans exigence de majuscule, chiffre, ou caractère spécial.
**Justification** : les recommandations NIST SP 800-63B et OWASP privilégient la longueur
du mot de passe plutôt que des règles arbitraires de complexité, qui poussent souvent vers
des mots de passe prévisibles et encouragent la réutilisation de variantes entre plusieurs
sites. La longueur reste le facteur le plus déterminant contre une attaque par force brute.

## D14 — Hors scope : attaques par mesure de temps de réponse sur /login
**Décision** : ce test ne traite pas les attaques par timing (timing attacks) sur
l'endpoint login.
**Justification** : une protection complète nécessiterait un appel factice à bcrypt même
lorsque l'utilisateur n'existe pas, afin d'uniformiser le temps de réponse dans tous les cas.
Complexité jugée disproportionnée par rapport au scope de ce test technique.

## D15 — UUID comme clé primaire
**Décision** : les utilisateurs sont identifiés par un UUID plutôt qu'un entier
auto-incrémenté.
**Justification** : les UUID évitent l'énumération triviale des identifiants, facilitent
une évolution vers une architecture distribuée, et constituent aujourd'hui un standard
largement adopté dans les API modernes.

## D16 — SQLAlchemy 2.0
**Décision** : le projet utilise la syntaxe SQLAlchemy 2.0 (`Mapped[]`, `mapped_column`,
`DeclarativeBase`).
**Justification** : cette syntaxe apporte un typage plus précis, une meilleure intégration
avec les outils de développement, et correspond aux recommandations officielles pour les
nouveaux projets.

## D17 — JWT minimal
**Décision** : le JWT contient uniquement `sub`, `type`, `iat`, `exp`.
**Justification** : le token ne contient aucune information métier (email, nom...) afin
d'éviter la duplication de données et de garantir que les informations utilisateur
proviennent toujours de la base de données.

## D18 — bcrypt
**Décision** : les mots de passe sont protégés avec bcrypt.
**Justification** : bcrypt intègre automatiquement un salt, est largement audité, et
constitue une référence reconnue pour la protection des mots de passe.

## D19 — FastAPI retenu comme framework
**Décision** : le backend est développé avec FastAPI (Python), alors que l'offre acceptait
toute technologie.
**Justification** : FastAPI fournit une validation native via Pydantic (utilisée massivement
dans ce projet, cf. D13, D15-D18), une documentation OpenAPI/Swagger générée automatiquement
sans effort supplémentaire, un typage Python strict qui réduit les erreurs à l'exécution, et
des performances comparables aux frameworks asynchrones les plus rapides du marché. Comparé
à Django (plus lourd, orienté monolithe avec ORM et admin intégrés, peu justifié pour une API
REST de 4 endpoints) ou Flask (plus minimaliste mais sans validation ni typage natifs,
nécessitant des dépendances supplémentaires pour obtenir des garanties équivalentes), FastAPI
offre le meilleur compromis entre rapidité de développement et rigueur pour ce périmètre.

---

*(Ce fichier sera complété à chaque étape du projet.)*
