from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import books, users, authors, genres, storage, reviews, search
from app.utils import create_tables, close_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    search.init_elastic_indexing()
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
app.include_router(search.router)
app.include_router(users.router)
app.include_router(authors.router)
app.include_router(genres.router)
app.include_router(storage.router)
app.include_router(reviews.router)
