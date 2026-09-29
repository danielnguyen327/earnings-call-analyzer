from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Skip .env entries the app doesn't use instead of refusing to start.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    equibles_api_key: str
    database_url: str
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
