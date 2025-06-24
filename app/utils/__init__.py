from .crypt import *
from .database import *
from .unit_of_work import *


class CrudException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)
