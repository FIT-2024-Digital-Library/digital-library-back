import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import all_routers
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

for router in all_routers:
    app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=4)
