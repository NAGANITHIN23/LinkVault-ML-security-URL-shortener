from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://linkvault:dev_password_123@localhost:5432/linkvault_db"
    REDIS_URL: str = "redis://localhost:6379"
    BASE_URL: str = "http://localhost:8000"
    SHORT_CODE_LENGTH: int = 7
    
    class Config:
        env_file = ".env"

settings = Settings()