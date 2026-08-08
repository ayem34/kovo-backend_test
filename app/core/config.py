from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration centralisée de l'application, lue depuis les variables
    d'environnement (fichier .env en local, variables d'env réelles en
    production). Aucun secret n'est jamais codé en dur dans le code.
    """

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
