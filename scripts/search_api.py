import os
import openai
import psycopg2
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss

# Load environment variables and API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="podcast_etl",
    user="postgres",
    password="160803",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# --- Fetch transcriptions by topic ---
def fetch_transcriptions_by_topic(topic):
    cursor.execute("SELECT filename, text, audio_url, topic FROM transcriptions WHERE topic = %s", (topic,))
    return cursor.fetchall()

# --- Get sentence embedding ---
def get_embedding(text):
    return model.encode(text)

# --- Find the best match for the query ---
def get_best_match(query, transcriptions):
    query_embedding = get_embedding(query)

    texts = [row[1] for row in transcriptions]
    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")

    # FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    query_embedding = np.array(query_embedding).reshape(1, -1)
    distances, indices = index.search(query_embedding, 1)

    best_idx = indices[0][0]
    score = distances[0][0]

    filename, text, audio_url, topic = transcriptions[best_idx]
    return {
        "filename": filename,
        "text": text,
        "audio_url": audio_url,
        "score": float(score),
        "topic": topic if topic else "N/A"
    }

# --- Main search function used in frontend ---
def streamlit_search(query, topic):
    transcriptions = fetch_transcriptions_by_topic(topic)
    if not transcriptions:
        return {"error": "No transcriptions found for this topic."}
    return get_best_match(query, transcriptions)

# --- Placeholder for transcription logic ---
def transcribe_file(file_path, topic=None):
    # This function can be replaced with real transcription logic (e.g., AssemblyAI or OpenAI Whisper)
    filename = os.path.basename(file_path)
    audio_url = f"/{file_path}"  # if served locally via frontend
    return {
        "filename": filename,
        "text": f"Dummy transcription for {filename}",
        "topic": topic or "Unknown",
        "audio_url": audio_url
    }
