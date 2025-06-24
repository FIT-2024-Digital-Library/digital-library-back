from .authors import router as authors_router
from .books import router as books_router
from .complex_search import router as search_router
from .genres import router as genres_router
from .reviews import router as reviews_router
from .storage import router as storage_router
from .users import router as users_router


all_routers = [
    authors_router,
    books_router,
    search_router,
    genres_router,
    reviews_router,
    storage_router,
    users_router
]
