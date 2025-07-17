from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import psycopg2
import os
import requests
from datetime import datetime
import time

app = Flask(__name__)

# Define base directory and model path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "models"))

# Load FAISS index and mappings
index_path = os.path.join(MODEL_DIR, "transcriptions.index")
id_map_path = os.path.join(MODEL_DIR, "id_text_map.pkl")
index_id_map_path = os.path.join(MODEL_DIR, "faiss_index_id_map.pkl")

if not os.path.exists(index_path):
    raise FileNotFoundError(f"FAISS index not found at {index_path}")
if not os.path.exists(id_map_path):
    raise FileNotFoundError(f"ID-Text Map not found at {id_map_path}")
if not os.path.exists(index_id_map_path):
    raise FileNotFoundError(f"FAISS Index-ID Map not found at {index_id_map_path}")

faiss_index = faiss.read_index(index_path)

with open(id_map_path, "rb") as f:
    id_text_map = pickle.load(f)

with open(index_id_map_path, "rb") as f:
    faiss_index_id_map = pickle.load(f)

# Load SentenceTransformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Search function
def search_similar_texts(query, k=5):
    query_vector = model.encode([query])
    D, I = faiss_index.search(query_vector, k)
    results = []
    for idx in I[0]:
        text_id = faiss_index_id_map.get(idx)
        if text_id:
            text = id_text_map.get(text_id)
            if text:
                results.append({"text_id": text_id, "text": text})
    return results

# Search endpoint
@app.route("/search", methods=["POST"])
def streamlit_search():
    data = request.json
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    results = search_similar_texts(query)
    return jsonify({"results": results})

# Upload + Transcription endpoint
@app.route("/upload", methods=["POST"])
def transcribe_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    os.makedirs("audio_files", exist_ok=True)
    save_path = os.path.join("audio_files", file.filename)
    file.save(save_path)

    # Transcribe using AssemblyAI
    api_key = "b54d78abb6754c60a6d2be277ae1308a"
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }

    with open(save_path, "rb") as f:
        upload_response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"authorization": api_key},
            files={"file": f}
        )

    if upload_response.status_code != 200:
        return jsonify({"error": "Failed to upload audio to AssemblyAI"}), 500

    upload_url = upload_response.json()["upload_url"]

    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json={"audio_url": upload_url},
        headers=headers
    )

    if transcript_response.status_code != 200:
        return jsonify({"error": "Failed to start transcription"}), 500

    transcript_id = transcript_response.json()["id"]

    # Polling for completion
    while True:
        polling_response = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers
        )
        result = polling_response.json()
        status = result["status"]
        if status == "completed":
            text = result["text"]
            break
        elif status == "error":
            return jsonify({"error": "Transcription failed"}), 500
        time.sleep(3)

    # Insert transcript into PostgreSQL
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="podcast_etl",
            user="postgres",
            password="160803"
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO podcasts (filename, text, timestamp) VALUES (%s, %s, %s)",
            (file.filename, text, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database insert failed: {str(e)}"}), 500

    return jsonify({"message": "File transcribed and inserted successfully", "text": text})

# Run Flask server
if __name__ == "__main__":
    app.run(host="localhost", port=5000)
