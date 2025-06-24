from fastapi import APIRouter

from app.repositories.indexing import Indexing
from app.settings import elastic_cred

router = APIRouter(
    prefix='/complex_search',
    tags=['complex_search']
)


@router.get("/context", response_model=list[int])
async def context_search(query: str) -> list[int]:
    results: dict = await Indexing.context_search_books(query)
    return [int(book["_id"]) for book in results['hits']['hits']
                             if book["_score"] >= elastic_cred.min_content_score]


@router.get("/semantic", response_model=list[int])
async def semantic_search(query: str) -> list[int]:
    results: dict = await Indexing.semantic_search_books(query)
    return [int(book["_id"]) for book in results['hits']['hits']
                             if book["_score"] >= elastic_cred.min_semantic_score]
