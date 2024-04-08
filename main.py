

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from bson import ObjectId
import yaml
# Define your FastAPI app
app = FastAPI()
   # Load the configuration from the YAML file
with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Access the MongoDB URI from the configuration
mongodb_uri = config["books_api"]["mongodb_uri"]
# Connect to MongoDB Atlas
client = MongoClient(mongodb_uri)
db = client["library_management"]
books_collection = db["books"]


# Define Pydantic models for request and response schemas
class AuthorDetail(BaseModel):
    AuthorName: str
    country: str

class Book(BaseModel):
    BookName: str
    TotalPages: int
    AuthorDetail: AuthorDetail

class BookInfo(BaseModel):
    id: str
    BookName: str
    TotalPages: int
    AuthorDetail: AuthorDetail

# API endpoints
@app.post("/books/", response_model=BookInfo)
async def create_book(book: Book):
    inserted_book = books_collection.insert_one(book.dict())
    book_info = BookInfo(**book.dict(), id=str(inserted_book.inserted_id))
    return book_info


@app.get("/books/", response_model=List[BookInfo])
async def list_books(AuthorName: str = None,BookName: str = None):
    query = {}
    if AuthorName:
        query["AuthorDetail.AuthorName"] = AuthorName
    if BookName:
        query["BookName"] = BookName

    books = list(books_collection.find(query))
    book_infos = [BookInfo(**book, id=str(book['_id'])) for book in books]
    return book_infos

@app.get("/books/{book_id}", response_model=BookInfo)
async def get_book(book_id: str):
    book_object_id = ObjectId(book_id)
    book = books_collection.find_one({"_id": book_object_id})
    if book:
        book_info = BookInfo(**book, id=str(book["_id"]))
        return book_info
    else:
        raise HTTPException(status_code=404, detail="Book not found")

@app.patch("/books/{book_id}", response_model=BookInfo)
async def update_book(book_id: str, book: Book):
    updated_book = books_collection.update_one({"_id": ObjectId(book_id)}, {"$set": book.dict()})
    if updated_book.modified_count == 1:
        return BookInfo(**book.dict(), id=book_id)
    else:
        raise HTTPException(status_code=404, detail="Book not found")

@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    deleted_book = books_collection.delete_one({"_id": ObjectId(book_id)})
    if deleted_book.deleted_count == 1:
        return {"message": "Book deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")



