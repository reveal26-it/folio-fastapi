
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/books")
def get_books():
    files = [f for f in os.listdir("static") if f.endswith(".json")]
    books = []
    for f in files:
        with open(f"static/{f}", "r") as file:
            data = json.load(file)
            books.append(data["book_info"])
    books.sort(key=lambda x: x["book_id"])
    return books

@app.get("/api/book/{book_name}")
def get_book(book_name: str):
    file_path = f"static/{book_name.lower().replace(' ', '_')}.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return {"error": "Book not found"}
