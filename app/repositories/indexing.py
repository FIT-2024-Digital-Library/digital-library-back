import asyncio, re, io, nltk, pdfplumber, string, urllib.parse
from concurrent.futures import ProcessPoolExecutor
from fastapi import HTTPException

from app.repositories.storage import Storage
from app.schemas import BookIndex
from app.settings.elastic import elastic_cred, _es


__all__ = ["Indexing"]


nltk.download('wordnet')
nltk.download('stopwords')


class Indexing:
    __english_stop_words = set(nltk.corpus.stopwords.words('english'))
    __executor = ProcessPoolExecutor(max_workers=4)

    @staticmethod
    def preprocess_text(text: str, remove_punctuation: bool = True):
        # Заменить \n и \t на пробел, убрать лишние пробелы
        text = re.sub(r'[\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        if remove_punctuation:
            translator = str.maketrans('', '', string.punctuation)
            text = text.translate(translator)
        return text.lower().strip()


    @staticmethod
    def extract_book_text(genre: str, content: bytes) -> dict:
        texts = []
        print("BOOK-PROCESSING: Start extracting")
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                raw_text = page.extract_text()
                if raw_text: texts.append(Indexing.preprocess_text(raw_text))
        print("BOOK-PROCESSING: Finish extracting")
        return {
            "genre": genre if genre is not None else '',
            "content": ' '.join(texts)
        }


    @classmethod
    async def index_book(cls, book_id: int, book: BookIndex):
        print("BOOK-PROCESSING: Start process")
        content = await Storage.download_file_bytes(urllib.parse.unquote(book.pdf_qname))
        loop = asyncio.get_running_loop()
        document = await loop.run_in_executor(
            Indexing.__executor, Indexing.extract_book_text,book.genre, content
        )
        try:
            await _es.index(index=elastic_cred.books_index, id=str(book_id), body=document)
        except Exception as e:
            print(f"Indexation error: {e}")
        print("BOOK-PROCESSING: Finish indexing")


    @classmethod
    async def delete_book(cls, book_id: int):
        try:
            if await _es.exists(index=elastic_cred.books_index, id=str(book_id)):
                await _es.delete(index=elastic_cred.books_index, id=str(book_id))
                print(f"BOOK-PROCESSING: Successfully deleted book with ID {book_id}")
        except Exception as e:
            raise HTTPException(status_code=418, detail=f"Deletion error: {e}")


    @classmethod
    async def context_search_books(cls, query):
        search_query = {
            "multi_match": {
                "query": Indexing.preprocess_text(query),
                "fields": ["genre", "content"],
                "type": "most_fields",
                "operator": "and",
                "fuzziness": "AUTO"
            }
        }
        return await _es.search(index=elastic_cred.books_index, query=search_query)


    @classmethod
    def __expand_and_filter_query(cls, query: str) -> str:
        query_words = set([word for word in query.split() if word not in cls.__english_stop_words])
        related_terms = set()
        for word in query_words:
            for synset in nltk.corpus.wordnet.synsets(word):
                for lemma in synset.lemmas():
                    related_terms.add(lemma.name().replace('_', ' '))
                for hypernym in synset.hypernyms():
                    for hypernym_term in hypernym.lemma_names():
                        related_terms.add(hypernym_term.replace('_', ' '))
        print(f"BOOK-PROCESSING: Expanded query\n{related_terms}")
        return " ".join(query_words.union(related_terms))


    @classmethod
    async def semantic_search_books(cls, query: str):
        search_query = {
            "multi_match": {
                "query": cls.__expand_and_filter_query(Indexing.preprocess_text(query)),
                "fields": ["genre^3", "content"],
                "type": "most_fields",
                "operator": "or",
                "fuzziness": "AUTO"
            }
        }
        return await _es.search(index=elastic_cred.books_index, query=search_query)
