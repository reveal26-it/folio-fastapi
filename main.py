from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from supabase import create_client, Client
import json
import os
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key) if url and key else None

class PostCreate(BaseModel):
    content: str
    book_reference: str = ""

class ReactionCreate(BaseModel):
    post_id: str
    type: str = "like"

class LibraryUpload(BaseModel):
    title: str
    author: str
    type: str
    file_url: str = ""

class ProfileUpdate(BaseModel):
    username: str
    bio: str

class MarkCreate(BaseModel):
    book_name: str
    chapter: int
    verse_id: str
    word_id: str = ""
    mark_type: str = "highlight"
    note: str = ""

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
            return json.load(file)
    return {"error": "Book not found"}

# --- SOCIAL API ---
@app.get("/api/posts")
def get_posts():
    if not supabase: return []
    try:
        response = supabase.table("folio_posts").select("*, folio_profiles(username)").order("created_at", desc=True).limit(50).execute()
        posts = response.data
        for p in posts:
            react_res = supabase.table("folio_reactions").select("id").eq("post_id", p["id"]).execute()
            p["reaction_count"] = len(react_res.data)
        return posts
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/posts")
def create_post(post: PostCreate):
    if not supabase: return {"error": "DB not connected"}
    try:
        user_res = supabase.table("folio_profiles").select("id").eq("username", "Victor").execute()
        if not user_res.data:
            new_user = supabase.table("folio_profiles").insert({"username": "Victor", "bio": "Founder of FOLIO"}).execute()
            user_id = new_user.data[0]["id"]
        else:
            user_id = user_res.data[0]["id"]
        response = supabase.table("folio_posts").insert({
            "user_id": user_id, "content": post.content, "book_reference": post.book_reference
        }).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/reactions")
def add_reaction(reaction: ReactionCreate):
    if not supabase: return {"error": "DB not connected"}
    try:
        supabase.table("folio_reactions").insert({"post_id": reaction.post_id, "type": reaction.type}).execute()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

# --- LIBRARY API ---
@app.get("/api/library")
def get_library():
    if not supabase: return []
    try:
        response = supabase.table("folio_library").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/library/upload")
def upload_to_library(item: LibraryUpload):
    if not supabase: return {"error": "DB not connected"}
    try:
        response = supabase.table("folio_library").insert({
            "title": item.title, "author": item.author, "type": item.type, "file_url": item.file_url
        }).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}

# --- PROFILE API ---
@app.get("/api/profile")
def get_profile():
    if not supabase: return {}
    try:
        response = supabase.table("folio_profiles").select("*").eq("username", "Victor").execute()
        if response.data: return response.data[0]
        return {}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/profile/update")
def update_profile(profile: ProfileUpdate):
    if not supabase: return {"error": "DB not connected"}
    try:
        existing = supabase.table("folio_profiles").select("id").eq("username", "Victor").execute()
        if existing.data:
            supabase.table("folio_profiles").update({"username": profile.username, "bio": profile.bio}).eq("username", "Victor").execute()
        else:
            supabase.table("folio_profiles").insert({"username": profile.username, "bio": profile.bio}).execute()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

# --- MARKS API (Highlights, Notes, Notables) ---
@app.post("/api/marks")
def add_mark(mark: MarkCreate):
    if not supabase: return {"error": "DB not connected"}
    try:
        supabase.table("folio_marks").insert({
            "book_name": mark.book_name, "chapter": mark.chapter, "verse_id": mark.verse_id,
            "word_id": mark.word_id, "mark_type": mark.mark_type, "note": mark.note
        }).execute()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/marks/{book_name}/{chapter}")
def get_marks(book_name: str, chapter: int):
    if not supabase: return []
    try:
        response = supabase.table("folio_marks").select("*").eq("book_name", book_name).eq("chapter", chapter).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/marks/{mark_id}")
def delete_mark(mark_id: str):
    if not supabase: return {"error": "DB not connected"}
    try:
        supabase.table("folio_marks").delete().eq("id", mark_id).execute()
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}
