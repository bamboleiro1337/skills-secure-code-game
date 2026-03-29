from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://buyuser:buypass@localhost:5432/buydb"
    secret_key: str = "dev-only-secret-change-before-deploying"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
