import psycopg2
import os
import pickle
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ---------- Define path to models directory ----------
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(models_dir, exist_ok=True)

# ---------- Connect to PostgreSQL and fetch transcriptions ----------
conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()
cur.execute("SELECT id, text FROM transcriptions WHERE text IS NOT NULL")
rows = cur.fetchall()
cur.close()
conn.close()

# ---------- Prepare IDs and corresponding texts ----------
ids = [row[0] for row in rows]
texts = [row[1].strip() for row in rows]

# ---------- Generate embeddings ----------
model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # Can change model if needed
embeddings = model.encode(texts, show_progress_bar=True)

# Convert to float32 and normalize
embeddings_np = np.array(embeddings).astype('float32')
embeddings_np = embeddings_np / np.linalg.norm(embeddings_np, axis=1, keepdims=True)

# ---------- Create and store FAISS index ----------
index = faiss.IndexFlatIP(embeddings_np.shape[1])  # IP = cosine similarity for normalized vectors
index.add(embeddings_np)
faiss.write_index(index, os.path.join(models_dir, "transcriptions.index"))

# ---------- Save ID-embedding & text maps ----------
with open(os.path.join(models_dir, "faiss_index_id_map.pkl"), "wb") as f:
    pickle.dump(ids, f)

with open(os.path.join(models_dir, "id_text_map.pkl"), "wb") as f:
    pickle.dump(dict(zip(ids, texts)), f)

print("✅ Embeddings generated and FAISS index saved successfully!")
