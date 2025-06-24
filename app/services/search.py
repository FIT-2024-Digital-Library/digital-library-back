from app.repositories import Indexing
from app.settings import elastic_cred


__all__ = ["SearchService"]


class SearchService:
    @staticmethod
    async def context_search(query: str) -> list[int]:
        results: dict = await Indexing.context_search_books(query)
        return [int(book["_id"]) for book in results['hits']['hits']
                                 if book["_score"] >= elastic_cred.min_content_score]

    @staticmethod
    async def semantic_search(query: str) -> list[int]:
        results: dict = await Indexing.semantic_search_books(query)
        return [int(book["_id"]) for book in results['hits']['hits']
                                 if book["_score"] >= elastic_cred.min_semantic_score]
