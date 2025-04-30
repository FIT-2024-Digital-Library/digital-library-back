import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import books, complex_search, users, authors, genres, storage, reviews
from app.settings import init_elastic_indexing
from app.utils import create_tables, close_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_elastic_indexing()
    await create_tables()
    yield
    await close_connections()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(books.router)
app.include_router(complex_search.router)
app.include_router(users.router)
app.include_router(authors.router)
app.include_router(genres.router)
app.include_router(storage.router)
app.include_router(reviews.router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2)
