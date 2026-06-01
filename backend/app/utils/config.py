from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    vision_ocr_api_key: str = ""
    vision_ocr_base_url: str = "https://api.openclawplan.com"
    vision_ocr_model: str = "gpt-5.5-xhigh"
    vision_ocr_timeout: int = 60
    vision_ocr_enabled: bool = True
    baidu_app_id: str = ""
    baidu_api_key: str = ""
    baidu_secret_key: str = ""
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
