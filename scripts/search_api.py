from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import shutil
import os

app = FastAPI()

# Allow CORS so frontend can access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 Mock Search Endpoint
class SearchQuery(BaseModel):
    query: str
    topic: str = None

@app.post("/search")
def search_podcasts(query: SearchQuery):
    # ⚠️ This is a placeholder result, just for demo
    return {
        "results": [
            {
                "filename": "demo_podcast.mp3",
                "topic": query.topic or "AI",
                "score": 0.97,
                "text": f"Sample result for query: '{query.query}'"
            }
        ]
    }

# 📤 Upload Endpoint (kept lightweight)
@app.post("/upload")
def upload_file(file: UploadFile = File(...), topic: str = Form(...)):
    # Save the uploaded file temporarily
    save_dir = f"audio_files/{topic}"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Skip actual transcription for now
    return {"message": "File uploaded successfully (mocked transcription not triggered)."}