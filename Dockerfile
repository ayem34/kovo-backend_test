FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Applique les migrations en attente puis démarre l'API. Faire ça au
# démarrage du conteneur (plutôt qu'en étape séparée manuelle) garantit
# que le comportement est identique en local (docker-compose) et en
# production (Render, étape 18) - un seul et même point d'entrée.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
