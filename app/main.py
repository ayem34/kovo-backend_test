from fastapi import FastAPI

from app.modules.users.router import router as users_router

app = FastAPI(
    title="Kôvo Backend Test API",
    description="API REST pour le test technique backend : inscription, connexion, gestion de profil.",
    version="1.0.0",
)

app.include_router(users_router)


@app.get("/")
def health_check():
    """Endpoint racine simple, utile pour vérifier que le déploiement fonctionne."""
    return {"status": "ok"}
