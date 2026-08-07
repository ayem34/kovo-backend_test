# DECISIONS.md — Journal des décisions d'architecture

Ce document trace les choix techniques et fonctionnels effectués pendant le développement,
avec leur justification. Objectif : que n'importe quel relecteur comprenne le "pourquoi"
derrière chaque décision, pas seulement le "quoi".

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
ça dans une route générique de mise à jour de profil est une mauvaise pratique. Un
endpoint dédié (`PUT /api/profile/password`) serait la bonne approche en production,
mais reste hors du scope strict demandé ici.

## D4 — L'email n'est pas modifiable via `PUT /api/profile`
**Décision** : l'email est en lecture seule après l'inscription.
**Justification** : le rendre modifiable impliquerait de re-vérifier l'unicité en base
à chaque update (race conditions possibles), potentiellement une re-validation du format,
et dans un vrai produit une confirmation par email. Complexité disproportionnée par
rapport au scope du test. Choix assumé et documenté plutôt que bricolé.

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
au lieu de naviguer entre plusieurs dossiers techniques. Ce pattern scale naturellement si
d'autres domaines métier sont ajoutés plus tard (ex: `products/`, `orders/`). Pour ce test
(un seul module `users`), le bénéfice est surtout un signal de maturité architecturale plutôt
qu'une nécessité stricte — choix assumé.

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
**Justification** : évite d'introduire un `Optional[datetime]` qui se propagerait dans le
schéma Pydantic (`UserOut`), les tests, et tout consommateur de l'API. C'est aussi la
convention par défaut de la plupart des ORMs (ActiveRecord, Django, Laravel) — cohérence
avec l'écosystème plutôt que sémantique "NULL = jamais modifié" plus rare en pratique.

## D12 — Driver PostgreSQL : psycopg3 plutôt que psycopg2
**Décision** : le projet utilise `psycopg[binary]` (psycopg 3.x) au lieu de `psycopg2-binary`,
initialement prévu.
**Justification** : `psycopg2` est en mode maintenance depuis plusieurs années ; `psycopg3` est
le driver officiellement recommandé pour les nouveaux projets SQLAlchemy 2.0. Le changement a
été déclenché par un bug d'encodage connu des wheels Windows de `psycopg2` (UnicodeDecodeError
lors de la négociation de connexion sur certains systèmes non-anglophones), mais reste un choix
justifié indépendamment de ce bug : implémentation plus moderne, activement maintenue, meilleure
compatibilité multiplateforme.

## D12 — Driver PostgreSQL : psycopg3 plutôt que psycopg2
**Décision** : le projet utilise `psycopg[binary]` (psycopg3) au lieu de `psycopg2-binary`,
initialement prévu dans le choix de stack.
**Justification** : bug non résolu et documenté (fermé "not planned" par les mainteneurs) de
`psycopg2` sur Windows, provoquant un `UnicodeDecodeError` lors de la connexion selon la
configuration locale du système. `psycopg2` est aujourd'hui en mode maintenance uniquement ;
`psycopg` (psycopg3) est la version activement développée et recommandée par l'écosystème
PostgreSQL/Python. Le changement se limite au préfixe `postgresql+psycopg://` dans
`DATABASE_URL` et à `requirements.txt` — aucune ligne de code applicatif n'a dû être modifiée,
ce qui valide a posteriori la séparation en couches (le driver est un détail d'infrastructure
isolé derrière SQLAlchemy).

## D13 — Pas de règle de complexité forcée sur le mot de passe
**Décision** : le mot de passe est contraint uniquement en longueur (8 à 72 caractères),
sans exigence de majuscule, chiffre, ou caractère spécial.
**Justification** : les recommandations modernes de sécurité (NIST SP 800-63B, OWASP)
déconseillent les règles de complexité forcée, qui poussent les utilisateurs vers des mots
de passe prévisibles (ex: "Password1!") et encouragent la réutilisation de variantes entre
plusieurs sites. La longueur est le facteur le plus déterminant contre une attaque par force
brute, pas la composition en catégories de caractères. Ce choix reste assumé et documenté
plutôt qu'un oubli.

## D14 — Limite connue : timing attack théorique sur /login
**Décision** : pas de correctif appliqué contre les attaques par mesure de temps de réponse
(timing attack) sur l'endpoint login.
**Justification** : quand l'email n'existe pas, la fonction retourne immédiatement sans
appeler `verify_password` (qui prend un temps mesurable à cause du coût volontaire de bcrypt).
Un attaquant très minutieux pourrait théoriquement mesurer cette différence de temps de
réponse pour déduire si un email existe en base, malgré le message d'erreur identique.
Corriger ça nécessiterait un appel factice à bcrypt même quand l'utilisateur n'existe pas —
complexité jugée disproportionnée pour ce test technique. Limite connue et assumée plutôt
qu'un oubli.

---

*(Ce fichier sera complété à chaque étape du projet.)*
