# Digital Library

Backend Docs: [![](https://deepwiki.com/badge.svg)](https://deepwiki.com/FIT-2024-Digital-Library/digital-library-back)

Frontend Docs: [![](https://deepwiki.com/badge.svg)](https://deepwiki.com/FIT-2024-Digital-Library/digital-library-front)

## Technology Stack and Features

- [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
- [SQLAlchemy](https://https://www.sqlalchemy.org/) for the Python SQL database interactions.
- [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
- [PostgreSQL 17](https://www.postgresql.org) as the SQL database.
- [MinIO](https://min.io/docs/minio/linux/operations/installation.html) as S3-compatible object storage with [wrapper for Python](https://min.io/docs/minio/linux/developers/python/API.html)
- [Elasticsearch](https://www.elastic.co/elasticsearch) for semantic search.

## How to deploy the service

1. Execute next commands locating in project's root:
```bash
# To create a virtual environment, you can use the venv module that comes with Python
python -m venv .venv

# Activate the new virtual environment
# - On Windows PowerShell, run
.venv\Scripts\activate
# - On Unix or MacOs, run
source .venv/bin/activate
# Upgrade pip
python -m pip install --upgrade pip

# Install packages from requirements.txt
pip install -r requirements.txt
```

2. Это пункт необходим для корректной работы `docker compose`. Определите `.env` файл в корневой директории проекта, либо экспортируйте в терминальную сессию переменные окружения. Необходимо задать следующие значения:
```conf
MINIO_VOLUME_PATH=...  # Стандартное расположение докер тома для хранилища объектов
MINIO_PORT=...  # Порт API хранилища
MINIO_BROWSER_PORT=...  # Порт для доступа к MinIO Console - GUI хранилища

POSTGRES_VOLUME_PATH=...
POSTGRES_HOST_PORT=...

YJS_WEBSOCKET_PORT=...
```
- `minio-server.env`:
```conf
MINIO_ROOT_USER=<root_user_login>
MINIO_ROOT_PASSWORD=<root_user_passwrod>
MINIO_VOLUMES=/data  # Better use this value
```

3. Add config files into folder `config/`:
- `minio-client.env`:
```conf
MINIO_HOSTNAME=<minio_addr>  # IP address
MINIO_PORT=<minio_port>
MINIO_BUCKET_NAME=<bucket_name>
MINIO_LOGIN=<backend_minio_user_login>
MINIO_PASSWORD=<backend_minio_user_password>
```
- `postgres.env`:
```conf
POSTGRES_USER=<backend_postgres_user_login>
POSTGRES_PASSWORD=<backend_postgres_user_passwrod>
POSTGRES_HOST=<postgres_addr>
POSTGRES_HOST_PORT=<postgres_port>
POSTGRES_DB=<postgres_db_name>
```
- `auth.env`:
```conf
SECRET_KEY=<secret_key_for_encrypting>
ALGORITHM=<encrypting_algorithm: e.g. HS256>
```

4. Run service:

Deploy
```bash
python -m app.main
```

Develop
```bash
fastapi dev app/main.py
```
