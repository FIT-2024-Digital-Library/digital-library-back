from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas import FileUploadedScheme, User, PrivilegesEnum
from app.services import StorageService
from app.utils.auth import user_has_permissions


router = APIRouter(
    prefix='/storage',
    tags=['storage']
)


@router.post("/", response_model=FileUploadedScheme, summary="Uploads new file. Privileged users only.")
def upload_file(
        file: UploadFile = File(...), user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)
):
    return StorageService.upload_file(file)


@router.get("/download/{filename}", response_class=StreamingResponse)
def download_file(filename: str):
    return StorageService.download_file(filename)


@router.get("/list", response_model=list[FileUploadedScheme])
def list_files():
    return StorageService.list_files()


@router.delete("{filename}", status_code=200, summary="Deletes file. Privileged users only.")
def delete_file(filename: str, user_data: User = user_has_permissions(PrivilegesEnum.MODERATOR)):
    return StorageService.delete_file(filename)
