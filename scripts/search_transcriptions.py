def semantic_search(query=None):
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
        index_to_dbid = pickle.load(f)  # List: index position → DB ID

    with open(os.path.join(models_dir, "id_text_map.pkl"), "rb") as f:
        dbid_to_text = pickle.load(f)   # Dict: DB ID → Text

    # ---------- Load embedding model ----------
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # ---------- Get user query ----------
    if query is None:
        query = input("🔍 Enter your search query: ")
    embedding = model.encode([query], normalize_embeddings=True).astype('float32')

    # ---------- Search in FAISS ----------
    D, I = index.search(embedding, k=5)
    threshold = 0.25  # Increased for more accuracy

    # ---------- Connect to DB ----------
    conn = psycopg2.connect(
        host="localhost",
        database="podcast_etl",
        user="postgres",
        password="160803"
    )
    cur = conn.cursor()

    found_match = False

    for faiss_idx, score in zip(I[0], D[0]):
        if faiss_idx == -1 or score < threshold:
            continue

        matched_db_id = index_to_dbid[faiss_idx]
        matched_text = dbid_to_text.get(matched_db_id, "[Text not found]")

        cur.execute("SELECT filename, topic FROM transcriptions WHERE id = %s", (matched_db_id,))
        result = cur.fetchone()

        if result:
            filename, topic = result
        else:
            filename = topic = "Unknown"

        print("\n🎯 Match Found:")
        print(f"📂 File: {filename}")
        print(f"🏷️ Topic: {topic}")
        print(f"📊 Score: {score:.4f}")
        print(f"📝 Transcription: {matched_text[:300]}...\n")

        found_match = True

    cur.close()
    conn.close()

    if not found_match:
        print("❌ No relevant match found.")

# ---------- Add CLI usage ----------
if __name__ == "__main__":
    semantic_search()
