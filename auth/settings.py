from pydantic import BaseSettings


class Settings(BaseSettings):
    project_id: str
    kite_api_key_secret_id: str = "kite-api-key"
    kite_api_secret_secret_id: str = "kite-api-secret"
    kite_access_token_secret_id: str = "kite-access-token"
    kite_refresh_token_secret_id: str = "kite-refresh-token"

    class Config:
        env_file = ".env"


settings = Settings()
