from elasticsearch import Elasticsearch
from fastapi import APIRouter, BackgroundTasks, UploadFile, File
#from sentence_transformers import SentenceTransformer
import pdfplumber
import io


router = APIRouter(
    prefix='/search',
    tags=['search']
)


ELASTIC_API_PORT = 9200

"""
# Загрузка модели
__model = SentenceTransformer('all-MiniLM-L6-v2')  # Модель с размером вектора 384

def encode_text_to_vector(text: str):
    return __model.encode(text).tolist()  # Преобразуем в список для сохранения
"""

# Подключение к Elasticsearch
es = Elasticsearch(f"http://84.237.53.137:{ELASTIC_API_PORT}")

index_settings = {
    "settings": {
        "analysis": {
            "analyzer": {
                "default": {
                    "type": "standard"
                }
            }
        }
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "title": {"type": "text"},
            "author": {"type": "text"},
            "genre": {"type": "keyword"},
            "content": {"type": "text"}
        }
    }
}


def init_elastic_indexing():
    if not es.indices.exists(index="books"):
        es.indices.create(index="books", body=index_settings)


def extract_pdf_text(content: bytes) -> str:
    # Используем io.BytesIO для создания файлового объекта из содержимого
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    print("BOOK-PROCESSING: Finish extracting")
    return full_text


def index_book(book_id: str, title: str, author: str, genre: str, content: bytes):
    # Генерация вектора
    # content_vector = encode_text_to_vector(content)
    # Формирование документа
    book_text: str = extract_pdf_text(content)
    document = {
        "title": title,
        "author": author,
        "genre": genre,
        "content": book_text,
    }
    # Индексация с обработкой ошибок
    try:
        es.index(index="books", id=book_id, body=document)
        print("BOOK-PROCESSING: Finish indexing")
    except Exception as e:
        print(f"Ошибка индексации: {e}")


@router.post("/upload-pdf")
async def upload_file(book_id: str, title: str, author: str, genre: str,
                      background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Читаем содержимое файла
    content = await file.read()
    background_tasks.add_task(
        index_book,
        book_id=book_id,
        title=title,
        author=author,
        genre=genre,
        content=content
    )
    return {"filename": file.filename}


def search_books(query):
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "author^2", "genre", "content"]
            }
        }
    }
    return es.search(index="books", body=search_body)


@router.get("/find-book")
def find_books(query: str):
    results: dict = search_books(query)
    return results['hits']['hits']
