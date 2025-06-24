import os
from typing import AsyncGenerator, Any
from fastapi import UploadFile, HTTPException
from minio.datatypes import BaseHTTPResponse
from minio.error import S3Error
from minio.helpers import ObjectWriteResult

from app.settings import minio_client, minio_cred


class Storage:
    @classmethod
    def is_file_exists(cls, path_to_object: str) -> bool:
        try:
            return minio_client.stat_object(minio_cred.bucket_name, path_to_object) is not None
        except S3Error as _:
            return False

    @classmethod
    def __brute_force_path_select(cls, filename: str | None) -> str:
        if filename is None:
            raise HTTPException(status_code=415, detail="The uploaded file must have a name")
        path = filename
        name, extension = os.path.splitext(filename)
        index = 0
        while cls.is_file_exists(path):
            index += 1
            path = f"{name}_{index}{extension}"
        return path

    @classmethod
    def upload_file_to_s3(cls, file: UploadFile) -> ObjectWriteResult:
        try:
            file_path = cls.__brute_force_path_select(file.filename)
            return minio_client.put_object(minio_cred.bucket_name, file_path, file.file, file.size)
        except Exception as e:
            raise HTTPException(409, f"Failed to upload file: {str(e)}")

    # получить файл из ссылки: file_stream_generator(urllib.parse.unquote(book.pdf_qname))
    @classmethod
    async def file_stream_generator(cls, full_path: str) -> AsyncGenerator[bytes, Any]:
        file_response: BaseHTTPResponse = minio_client.get_object(minio_cred.bucket_name, full_path)
        try:
            for chunk in file_response.stream():
                yield chunk
        finally:
            file_response.close()
            file_response.release_conn()

    @classmethod
    async def download_file_bytes(cls, full_path: str) -> bytes:
        data = bytearray()
        async for chunk in cls.file_stream_generator(full_path):
            data.extend(chunk)
        return bytes(data)

    @classmethod
    def list_files_in_s3(cls):
        return minio_client.list_objects(minio_cred.bucket_name)

    @classmethod
    def delete_file_in_s3(cls, filename: str):
        try:
            minio_client.remove_object(minio_cred.bucket_name, filename)
        except Exception as e:
            raise HTTPException(409, f"Failed to delete file: {str(e)}")
