import urllib.parse
from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.schemas import FileUploadedScheme, User, PrivilegesEnum
from app.repositories import Storage


__all__ = ["StorageService"]


class StorageService:
    @staticmethod
    def upload_file(file: UploadFile) -> FileUploadedScheme:
        book_object = Storage.upload_file_to_s3(file)
        return FileUploadedScheme(qname=urllib.parse.quote(book_object.object_name))

    @staticmethod
    def download_file(filename: str) -> StreamingResponse:
        if not Storage.is_file_exists(filename):
            raise HTTPException(404, "File not found")
        return StreamingResponse(
            Storage.file_stream_generator(f"{filename}"),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={urllib.parse.quote(filename)}"}
        )

    @staticmethod
    def list_files() -> list[FileUploadedScheme]:
        return [
            FileUploadedScheme(qname=urllib.parse.quote(obj.object_name))
            for obj in Storage.list_files_in_s3()
        ]

    @staticmethod
    def delete_file(filename: str) -> Response:
        if not Storage.is_file_exists(filename):
            raise HTTPException(404, "File not found")
        Storage.delete_file_in_s3(filename)
        return Response(status_code=200)
