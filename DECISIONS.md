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

---

*(Ce fichier sera complété à chaque étape du projet.)*
