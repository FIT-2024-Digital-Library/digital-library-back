from urllib.parse import quote
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.schemas import FileUploadedScheme, User
from app.schemas.users import PrivilegesEnum
from app.utils.auth import user_has_permissions


from app.crud.storage import is_file_exists, upload_file_to_s3, file_stream_generator, list_files_in_s3, delete_file_in_s3

router = APIRouter(
    prefix='/storage',
    tags=['storage']
)


@router.post("/", response_model=FileUploadedScheme, summary="Uploads new file. Privileged users only.")
def upload_file(file: UploadFile = File(), user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    obj = upload_file_to_s3(file)
    return FileUploadedScheme(
        qname=quote(obj.object_name)
    )


@router.get("/download/{filename}", response_class=StreamingResponse)
def download_file(filename: str):
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
        FileUploadedScheme(qname=quote(obj.object_name))
        for obj in list_files_in_s3()
    ]


@router.delete("{filename}", status_code=200, summary="Deletes file. Privileged users only.")
def delete_file(filename: str, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    if not is_file_exists(filename):
        raise HTTPException(404, "File not found")
    delete_file_in_s3(filename)
    return Response(status_code=200)
