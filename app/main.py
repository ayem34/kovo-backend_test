from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.users.router import router as users_router

app = FastAPI(
    title="Kôvo Backend Test API",
    description="API REST pour le test technique backend : inscription, connexion, gestion de profil.",
    version="1.0.0",
)

app.include_router(users_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Filet de sécurité global : toute exception non prévue explicitement
    (bug, base de données indisponible, etc.) est interceptée ici plutôt
    que de laisser une trace Python brute remonter au client - ce qui
    exposerait des détails internes (chemins de fichiers, requêtes SQL...)
    et serait non professionnel. Le détail réel de l'erreur reste
    disponible dans les logs serveur (uvicorn l'affiche automatiquement),
    jamais dans la réponse HTTP.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue."},
    )


@app.get("/")
def health_check():
    """Endpoint racine simple, utile pour vérifier que le déploiement fonctionne."""
    return {"status": "ok"}
