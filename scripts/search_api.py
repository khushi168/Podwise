import os
import pickle
import time
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ASSEMBLYAI_API_KEY = "b54d78abb6754c60a6d2be277ae1308a"

# --- Semantic Search Function ---
def search_transcriptions(query: str, topic: str = None):
    models_dir = os.path.join(os.path.dirname(__file__), "../models")
    index = faiss.read_index(os.path.join(models_dir, "transcriptions.index"))

    with open(os.path.join(models_dir, "faiss_index_id_map.pkl"), "rb") as f:
        index_to_dbid = pickle.load(f)
    with open(os.path.join(models_dir, "id_text_map.pkl"), "rb") as f:
        dbid_to_text = pickle.load(f)

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode([query], normalize_embeddings=True).astype('float32')
    D, I = index.search(embedding, k=5)
    threshold = 0.15

    conn = psycopg2.connect(host="localhost", database="podcast_etl", user="postgres", password="160803")
    cur = conn.cursor()

    results = []
    for faiss_idx, score in zip(I[0], D[0]):
        if faiss_idx == -1 or score < threshold:
            continue

        matched_db_id = index_to_dbid[faiss_idx]
        matched_text = dbid_to_text.get(matched_db_id, "[Text not found]")

        if topic:
            cur.execute("SELECT filename, topic FROM transcriptions WHERE id = %s AND topic = %s", (matched_db_id, topic))
        else:
            cur.execute("SELECT filename, topic FROM transcriptions WHERE id = %s", (matched_db_id,))

        result = cur.fetchone()
        if not result:
            continue

        filename, topic_found = result
        results.append({
            "text": matched_text,
            "filename": filename,
            "topic": topic_found,
            "score": float(score)
        })

    cur.close()
    conn.close()
    return results

# --- Transcription Endpoint ---
@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    data = request.get_json()
    filepath = data.get("filepath")
    filename = data.get("filename")
    topic = data.get("topic")

    if not all([filepath, filename, topic]):
        return jsonify({"error": "Missing required data"}), 400

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        headers = {"authorization": ASSEMBLYAI_API_KEY}

        # Upload to AssemblyAI
        with open(filepath, "rb") as f:
            upload_res = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, files={"file": f})
        upload_res.raise_for_status()
        upload_url = upload_res.json()["upload_url"]

        # Start transcription
        transcript_res = requests.post("https://api.assemblyai.com/v2/transcript", json={"audio_url": upload_url}, headers=headers)
        transcript_res.raise_for_status()
        transcript_id = transcript_res.json()["id"]

        # Poll status
        while True:
            poll_res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
            poll_json = poll_res.json()
            if poll_json["status"] == "completed":
                transcript_text = poll_json["text"]
                break
            elif poll_json["status"] == "error":
                return jsonify({"error": poll_json["error"]}), 500
            time.sleep(3)

        # Save in PostgreSQL
        conn = psycopg2.connect(host="localhost", database="podcast_etl", user="postgres", password="160803")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transcriptions (transcript_id, audio_url, text, filename, topic)
            VALUES (%s, %s, %s, %s, %s)
        """, (transcript_id, upload_url, transcript_text, filename, topic))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Transcription and insertion successful"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Search Endpoint ---
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "")
    topic = data.get("topic", None)
    results = search_transcriptions(query, topic)

    if results:
        return jsonify({**results[0], "match_found": True})
    else:
        return jsonify({"match_found": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
