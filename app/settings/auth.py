from pydantic_settings import BaseSettings, SettingsConfigDict


__all__ = ["auth_cred"]


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="./config/auth.env")
    secret_key: str
    algorithm: str


auth_cred = AuthSettings()
