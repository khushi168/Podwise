import os
import psycopg2
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# ---------- Constants ----------
DB_CONFIG = {
    "host": "localhost",
    "database": "podcast_etl",
    "user": "postgres",
    "password": "160803"
}
MODEL_NAME = "paraphrase-MiniLM-L3-v2"  # lightweight model, change if needed

# ---------- Directory Setup ----------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ---------- Fetch Data from PostgreSQL ----------
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM transcriptions WHERE text IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    print("❌ Error fetching data from PostgreSQL:", e)
    exit(1)

if not rows:
    print("⚠️ No transcriptions found in the database.")
    exit(0)

ids = [row[0] for row in rows]
texts = [row[1].strip() for row in rows]

print(f"🔎 Loaded {len(texts)} transcriptions.")

# ---------- Load SentenceTransformer Model ----------
try:
    model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    print("❌ Error loading embedding model:", e)
    exit(1)

# ---------- Generate Embeddings ----------
print("📌 Generating sentence embeddings...")
embeddings = model.encode(texts, show_progress_bar=True)

# Convert to float32 and normalize for cosine similarity
embeddings_np = np.array(embeddings).astype("float32")
embeddings_np = embeddings_np / np.linalg.norm(embeddings_np, axis=1, keepdims=True)

# ---------- Create & Save FAISS Index ----------
index = faiss.IndexFlatIP(embeddings_np.shape[1])
index.add(embeddings_np)
faiss.write_index(index, os.path.join(MODELS_DIR, "transcriptions.index"))

# ---------- Save Mappings ----------
with open(os.path.join(MODELS_DIR, "faiss_index_id_map.pkl"), "wb") as f:
    pickle.dump(ids, f)

with open(os.path.join(MODELS_DIR, "id_text_map.pkl"), "wb") as f:
    pickle.dump(dict(zip(ids, texts)), f)

print("✅ FAISS index and mapping files saved successfully!")
