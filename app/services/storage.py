import urllib.parse
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.schemas import FileUploadedScheme, User, PrivilegesEnum
from app.utils.auth import user_has_permissions
from app.repositories import Storage


router = APIRouter(
    prefix='/storage',
    tags=['storage']
)


@router.post("/", response_model=FileUploadedScheme, summary="Uploads new file. Privileged users only.")
def upload_file(
        file: UploadFile = File(...),
        user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)
):
    book_object = Storage.upload_file_to_s3(file)
    return FileUploadedScheme(qname=urllib.parse.quote(book_object.object_name))


@router.get("/download/{filename}", response_class=StreamingResponse)
def download_file(filename: str):
    if not Storage.is_file_exists(filename):
        raise HTTPException(404, "File not found")
    return StreamingResponse(
        Storage.file_stream_generator(f"{filename}"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={urllib.parse.quote(filename)}"}
    )


@router.get("/list", response_model=list[FileUploadedScheme])
def list_files():
    return [
        FileUploadedScheme(qname=urllib.parse.quote(obj.object_name))
        for obj in Storage.list_files_in_s3()
    ]


@router.delete("{filename}", status_code=200, summary="Deletes file. Privileged users only.")
def delete_file(filename: str, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    if not Storage.is_file_exists(filename):
        raise HTTPException(404, "File not found")
    Storage.delete_file_in_s3(filename)
    return Response(status_code=200)
