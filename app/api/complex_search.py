from fastapi import APIRouter

from app.services import SearchService


router = APIRouter(
    prefix='/complex_search',
    tags=['complex_search']
)


@router.get("/context", response_model=list[int])
async def context_search(query: str) -> list[int]:
    return await SearchService.context_search(query)


@router.get("/semantic", response_model=list[int])
async def semantic_search(query: str) -> list[int]:
    return await SearchService.semantic_search(query)
