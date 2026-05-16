from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    port: int = 8000
    app_name: str = "GCode Converter"
    app_version: str = "1.0.0"
    debug: bool = True
    data_dir: str = "app/data"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
