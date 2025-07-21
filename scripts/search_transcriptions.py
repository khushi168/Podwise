def semantic_search(query=None):
    import os
    import pickle
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import psycopg2

    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    index = faiss.read_index(os.path.join(models_dir, "transcriptions.index"))

    with open(os.path.join(models_dir, "faiss_index_id_map.pkl"), "rb") as f:
        index_to_dbid = pickle.load(f)

    with open(os.path.join(models_dir, "id_text_map.pkl"), "rb") as f:
        dbid_to_text = pickle.load(f)

    model = SentenceTransformer('all-MiniLM-L6-v2')

    if query is None:
        return []

    embedding = model.encode([query], normalize_embeddings=True).astype('float32')
    D, I = index.search(embedding, k=5)
    threshold = 0.05

    conn = psycopg2.connect(
        host="localhost",
        database="podcast_etl",
        user="postgres",
        password="160803"
    )
    cur = conn.cursor()

    results = []
    for faiss_idx, score in zip(I[0], D[0]):
        if faiss_idx == -1:
            continue

        matched_db_id = index_to_dbid[faiss_idx]
        matched_text = dbid_to_text.get(matched_db_id, "[Text not found]")

        cur.execute("SELECT filename, topic FROM transcriptions WHERE id = %s", (matched_db_id,))
        result = cur.fetchone()
        if result:
            filename, topic = result
        else:
            filename = topic = "Unknown"

        results.append({
            "file": filename,
            "topic": topic,
            "score": float(score),
            "chunk": matched_text
        })

    cur.close()
    conn.close()
    return results
