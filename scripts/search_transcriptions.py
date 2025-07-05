import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2

# ---------- Load FAISS index ----------
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
index = faiss.read_index(os.path.join(models_dir, "transcriptions.index"))

# ---------- Load ID mappings ----------
with open(os.path.join(models_dir, "faiss_index_id_map.pkl"), "rb") as f:
    index_to_dbid = pickle.load(f)

with open(os.path.join(models_dir, "id_text_map.pkl"), "rb") as f:
    dbid_to_text = pickle.load(f)

# ---------- Load embedding model ----------
model = SentenceTransformer('all-MiniLM-L6-v2')

# ---------- Get user query ----------
query = input("🔍 Enter your search query: ")
print()
embedding = model.encode([query])
embedding = np.array(embedding).astype('float32')
embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)

# ---------- Search in FAISS ----------
D, I = index.search(embedding, k=5)  # Search top 5 to allow filtering
threshold = 0.22  # Adjust this value higher for stricter filtering

# ---------- Connect to DB ----------
conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()

# ---------- Display best matches ----------
found_any = False
shown = 0
shown_ids = set()

for faiss_idx, score in zip(I[0], D[0]):
    if faiss_idx == -1 or score < threshold:
        continue

    matched_db_id = index_to_dbid[faiss_idx]
    if matched_db_id in shown_ids:
        continue
    shown_ids.add(matched_db_id)

    matched_text = dbid_to_text.get(matched_db_id, "[Text not found]")

    # Fetch metadata
    cur.execute("SELECT filename, topic FROM transcriptions WHERE id = %s", (matched_db_id,))
    result = cur.fetchone()
    filename = result[0] if result else "Unknown"
    topic = result[1] if result and len(result) > 1 else "Unknown"

    print(f"🎯 Match #{shown + 1}")
    print(f"📂 File: {filename}")
    print(f"🏷️ Topic: {topic}")
    print(f"🔍 Score: {score:.4f}")
    print()
    print(f"📝 Transcription: {matched_text[:300]}...\n")

    found_any = True
    shown += 1

    if shown >= 2:  # Limit to 2 matches
        break

if not found_any:
    print("❌ No highly relevant result found.")

cur.close()
conn.close()
