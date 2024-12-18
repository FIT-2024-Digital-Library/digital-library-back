import os

from urllib.parse import quote
from typing import AsyncGenerator, Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.params import Depends
from fastapi.responses import StreamingResponse, Response
from minio.datatypes import BaseHTTPResponse
from minio.error import S3Error
from minio.helpers import ObjectWriteResult

from app.schemas import FileUploadedScheme, User
from app.schemas.users import PrivilegesEnum
from app.settings import minio_client, minio_cred
from app.utils.auth import get_current_user, user_has_permissions

router = APIRouter(
    prefix='/storage',
    tags=['storage']
)


def is_file_exists(path_to_object: str) -> bool:
    try:
        return minio_client.stat_object(minio_cred.bucket_name, path_to_object) is not None
    except S3Error as _:
        return False


@router.post("/", response_model=FileUploadedScheme, summary="Uploads new file. Privileged users only.")
def upload_file(file: UploadFile = File(), user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    full_path = file.filename
    name, extension = os.path.splitext(file.filename)
    index = 0
    while is_file_exists(full_path):
        index += 1
        full_path = f"{name}_{index}{extension}"
    try:
        obj: ObjectWriteResult = minio_client.put_object(
            minio_cred.bucket_name, full_path, file.file, file.size
        )
    except Exception as e:
        raise HTTPException(409, f"Failed to upload file: {str(e)}")
    return FileUploadedScheme(
        url=f"/storage/download/{quote(obj.object_name)}"
    )


async def file_stream_generator(full_path: str) -> AsyncGenerator[bytes, Any]:
    file_response: BaseHTTPResponse = minio_client.get_object(minio_cred.bucket_name, full_path)
    try:
        for chunk in file_response.stream():
            yield chunk
    finally:
        file_response.close()
        file_response.release_conn()


@router.get("/download/{filename}", response_class=StreamingResponse)
def download_file(filename: str, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    if not is_file_exists(filename):
        raise HTTPException(404, "File not found")
    return StreamingResponse(
        file_stream_generator(f"{filename}"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/list", response_model=list[FileUploadedScheme])
def list_files():
    return [
        FileUploadedScheme(url=f"/storage/{quote(obj.object_name)}")
        for obj in minio_client.list_objects(minio_cred.bucket_name)
    ]


@router.delete("{filename}", status_code=200, summary="Deletes file. Privileged users only.")
def delete_file(filename: str, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    if not is_file_exists(filename):
        raise HTTPException(404, "File not found")
    try:
        minio_client.remove_object(minio_cred.bucket_name, filename)
    except Exception as e:
        raise HTTPException(409, f"Failed to delete file: {str(e)}")
    return Response(status_code=200)
