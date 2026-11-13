from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/api/books")
def get_books():
    files = [f for f in os.listdir(".") if f.endswith(".json") and f != "folio_ledger_full.json"]
    books = []
    for f in files:
        try:
            with open(f, "r") as file:
                data = json.load(file)
                if "book_info" in data:
                    books.append(data["book_info"])
        except:
            pass
    books.sort(key=lambda x: x["book_id"])
    return books

@app.get("/api/book/{book_name}")
def get_book(book_name: str):
    file_path = f"{book_name.lower().replace(' ', '_')}.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    return {"error": "Book not found"}
