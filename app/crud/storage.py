import os
from typing import AsyncGenerator, Any
from fastapi import UploadFile, HTTPException, status
from minio.datatypes import BaseHTTPResponse
from minio.error import S3Error
from minio.helpers import ObjectWriteResult

from app.settings import minio_client, minio_cred


def is_file_exists(path_to_object: str) -> bool:
    try:
        return minio_client.stat_object(minio_cred.bucket_name, path_to_object) is not None
    except S3Error as _:
        return False


def __brute_force_path_select(filename: str | None):
    if filename is None:
        raise HTTPException(status_code=415, detail="Loaded file must to has a name")
    path = filename
    name, extension = os.path.splitext(filename)
    index = 0
    while is_file_exists(path):
        index += 1
        path = f"{name}_{index}{extension}"
    return path


def upload_file_to_s3(file: UploadFile) -> ObjectWriteResult:
    full_path = __brute_force_path_select(file.filename)
    try:
        return minio_client.put_object(
            minio_cred.bucket_name, full_path, file.file, file.size
        )
    except Exception as e:
        raise HTTPException(409, f"Failed to upload file: {str(e)}")


# получить файл из ссылки: file_stream_generator(urllib.parse.unquote(book.pdf_qname))
async def file_stream_generator(full_path: str) -> AsyncGenerator[bytes, Any]:
    file_response: BaseHTTPResponse = minio_client.get_object(minio_cred.bucket_name, full_path)
    try:
        for chunk in file_response.stream():
            yield chunk
    finally:
        file_response.close()
        file_response.release_conn()


def list_files_in_s3():
    return minio_client.list_objects(minio_cred.bucket_name)


def delete_file_in_s3(filename: str):
    try:
        minio_client.remove_object(minio_cred.bucket_name, filename)
    except Exception as e:
        raise HTTPException(409, f"Failed to delete file: {str(e)}")