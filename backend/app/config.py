from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    alpha_vantage_api_key: str
    anthropic_api_key: str
    database_url: str
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
