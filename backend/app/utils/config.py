from pydantic_settings import BaseSettings


_EXAMPLE_SECRETS = {
    "您的_API_Key",
    "您的_OpenClawPlan_API_Key",
    "您的API_Key",
    "您的App_ID",
    "您的Secret_Key",
    "请替换为随机强密钥",
}


def is_configured_secret(value: str) -> bool:
    return bool(value and value.strip() not in _EXAMPLE_SECRETS)


class Settings(BaseSettings):
    vision_ocr_api_key: str = ""
    vision_ocr_base_url: str = "https://api.apiyi.com"
    vision_ocr_model: str = "gpt-5.6-terra"
    vision_ocr_timeout: int = 60
    vision_ocr_enabled: bool = True
    port: int = 8000
    app_name: str = "GCode Converter"
    app_version: str = "1.0.0"
    debug: bool = False
    data_dir: str = "app/data"
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
