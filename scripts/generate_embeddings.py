import psycopg2
import os
import pickle
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# ----------- Setup paths -----------

models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(models_dir, exist_ok=True)

# ----------- Load data from DB -----------

conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()
cur.execute("SELECT id, text FROM transcriptions")
rows = cur.fetchall()
cur.close()
conn.close()

# ----------- Prepare data -----------

ids = [row[0] for row in rows]
texts = [row[1] for row in rows]

# ----------- Generate embeddings -----------

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)
embeddings_np = np.array(embeddings).astype('float32')
embeddings_np = embeddings_np / np.linalg.norm(embeddings_np, axis=1, keepdims=True)

# ----------- Build and save FAISS index -----------

index = faiss.IndexFlatIP(embeddings_np.shape[1])
index.add(embeddings_np)
faiss.write_index(index, os.path.join(models_dir, "transcriptions.index"))

# ----------- Save mapping files -----------

with open(os.path.join(models_dir, "faiss_index_id_map.pkl"), "wb") as f:
    pickle.dump(ids, f)

with open(os.path.join(models_dir, "id_text_map.pkl"), "wb") as f:
    pickle.dump(dict(zip(ids, texts)), f)

print("✅ Embeddings & FAISS index saved!")
