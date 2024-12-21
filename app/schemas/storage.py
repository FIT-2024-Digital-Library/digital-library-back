from .base import CamelCaseBaseModel

__all__ = ["FileUploadedScheme"]


class FileUploadedScheme(CamelCaseBaseModel):
    qname: str
