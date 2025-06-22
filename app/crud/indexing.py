import re, io, nltk, pdfplumber
from fastapi import HTTPException

from app.crud.storage import Storage
from app.settings.elastic import elastic_cred, _es

nltk.download('wordnet')
nltk.download('stopwords')


class Indexing:
    __english_stop_words = set(nltk.corpus.stopwords.words('english'))

    @classmethod
    def __extract_pdf_text(cls, content: bytes) -> str:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        print("BOOK-PROCESSING: Finish extracting")
        return full_text

    @classmethod
    def __preprocess_text(cls, text: str, remove_punctuation: bool = True):
        text = text.replace("\n", " ").replace("\t", " ")
        text = re.sub(r'\s+', ' ', text)  ## лишние пробелы

        if remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)

        text = text.lower()
        return text

    @classmethod
    async def index_book(cls, book_id: int, genre: str, book_file_path: str):
        document = {
            "genre": genre if genre is not None else "",
            "content": cls.__preprocess_text(cls.__extract_pdf_text(
                await Storage.download_file_bytes(book_file_path)
            ))
        }
        try:
            await _es.index(index=elastic_cred.books_index, id=str(book_id), body=document)
            print("BOOK-PROCESSING: Finish indexing")
        except Exception as e:
            raise HTTPException(status_code=418, detail=f"Indexation error: {e}")

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
                "query": cls.__preprocess_text(query),
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
                "query": cls.__expand_and_filter_query(cls.__preprocess_text(query)),
                "fields": ["genre^3", "content"],
                "type": "most_fields",
                "operator": "or",
                "fuzziness": "AUTO"
            }
        }
        return await _es.search(index=elastic_cred.books_index, query=search_query)
