from minio import Minio
from pydantic_settings import BaseSettings, SettingsConfigDict


__all__ = ["minio_client", "minio_cred"]


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='MINIO_', env_file="./config/minio-client.env")

    bucket_name: str
    hostname: str
    port: int
    login: str
    password: str

    @property
    def minio_url(self) -> str:
        """Hostname with port"""
        return f"{self.hostname}:{self.port}"


minio_cred = MinioSettings()

minio_client = Minio(
    minio_cred.minio_url,
    access_key=minio_cred.login,
    secret_key=minio_cred.password,
    secure=False
)
