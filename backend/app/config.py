from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str
    MOODLE_TOKEN: str
    MOODLE_API_URL: str 
    DATABASE_PATH: str = "tasks.db"

    # Se lee el archivo .env ubicado en la carpeta raíz de la carpeta backend/
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()