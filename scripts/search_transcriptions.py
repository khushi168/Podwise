import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2

# Load models directory
models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

# Load FAISS index
index = faiss.read_index(os.path.join(models_dir, "transcriptions.index"))

# Load mapping from FAISS index to DB ID
with open(os.path.join(models_dir, "faiss_index_id_map.pkl"), "rb") as f:
    index_to_db_id = pickle.load(f)

# Load mapping from DB ID to text
with open(os.path.join(models_dir, "id_text_map.pkl"), "rb") as f:
    id_text_map = pickle.load(f)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Input query
query = input("Enter your search query: ")

# Convert query to embedding
query_vec = model.encode([query])
query_vec = np.array(query_vec).astype('float32')
query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

# Perform search
distances, indices = index.search(query_vec, k=1)

# Threshold
threshold = 0.1
faiss_idx = int(indices[0][0])
score = distances[0][0]

print("\nTop matching transcription:")
print(f"🔍 Match Score: {score:.4f}")

# Check match
if faiss_idx == -1 or score < threshold:
    print("No relevant result found for your query.")
else:
    db_id = index_to_db_id[faiss_idx]

    # Connect to DB to fetch filename
    conn = psycopg2.connect(
        host="localhost",
        database="podcast_etl",
        user="postgres",
        password="160803"
    )
    cur = conn.cursor()
    cur.execute("SELECT filename FROM transcriptions WHERE id = %s", (db_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    filename = result[0] if result else "Unknown"
    print(f"📂 File: {filename}")
    print(f"📝 Transcription: {id_text_map[db_id][:250]}...")
