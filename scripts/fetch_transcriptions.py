import os
import psycopg2
import requests
import time
import pickle
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss

# ------------------ Load environment variables ------------------
load_dotenv()
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# ------------------ Load Sentence Transformer ------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# ------------------ PostgreSQL Connection ------------------
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()

# ------------------ Delete transcriptions and FAISS entry ------------------
def delete_transcriptions_by_ids(ids):
    index_file = "models/faiss.index"
    mapping_file = "models/id_mapping.pkl"

    if os.path.exists(index_file) and os.path.exists(mapping_file):
        index = faiss.read_index(index_file)
        with open(mapping_file, "rb") as f:
            id_mapping = pickle.load(f)
    else:
        print("❌ FAISS index or ID mapping not found.")
        return

    to_delete_indices = []
    new_id_mapping = {}
    all_embeddings = []

    for faiss_id, fname in id_mapping.items():
        cur.execute("SELECT id, topic FROM transcriptions WHERE filename = %s", (fname,))
        result = cur.fetchone()
        if result and result[0] in ids:
            print(f"Deleting DB ID {result[0]}, File: {fname}")
            topic = result[1]
            file_path = os.path.join("audio_files", topic + "_cluster", fname)
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
            cur.execute("DELETE FROM transcriptions WHERE id = %s", (result[0],))
            conn.commit()
        else:
            vector = index.reconstruct(faiss_id)
            all_embeddings.append(vector)
            new_id_mapping[len(new_id_mapping)] = fname

    if all_embeddings:
        new_index = faiss.IndexFlatL2(384)
        new_index.add(np.array(all_embeddings).astype('float32'))
        faiss.write_index(new_index, index_file)
        with open(mapping_file, "wb") as f:
            pickle.dump(new_id_mapping, f)
        print("✅ FAISS index updated after deletion.")
    else:
        os.remove(index_file)
        os.remove(mapping_file)
        print("⚠️ All vectors removed. FAISS index deleted.")

# ------------------ Batch Transcription and Index ------------------
def transcribe_and_index(audio_base_folder="audio_files"):
    index_file = "models/faiss.index"
    mapping_file = "models/id_mapping.pkl"

    if os.path.exists(index_file):
        index = faiss.read_index(index_file)
        with open(mapping_file, "rb") as f:
            id_mapping = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(384)
        id_mapping = {}

    for topic_folder in os.listdir(audio_base_folder):
        topic_path = os.path.join(audio_base_folder, topic_folder)
        if not os.path.isdir(topic_path):
            continue

        topic = topic_folder.replace("_cluster", "")

        for filename in os.listdir(topic_path):
            if filename.endswith(".mp3"):
                cur.execute("SELECT 1 FROM transcriptions WHERE filename = %s", (filename,))
                if cur.fetchone():
                    print(f"⏩ Skipping {filename}, already in DB.")
                    continue

                audio_path = os.path.join(topic_path, filename)
                print(f"🎙️ Transcribing {filename} from topic '{topic}'...")

                with open(audio_path, 'rb') as f:
                    response = requests.post(
                        "https://api.assemblyai.com/v2/upload",
                        headers={"authorization": ASSEMBLYAI_API_KEY},
                        files={"file": f}
                    )
                if response.status_code != 200:
                    print("Upload failed:", response.status_code, response.text)
                    continue
                audio_url = response.json()["upload_url"]

                transcript_response = requests.post(
                    "https://api.assemblyai.com/v2/transcript",
                    json={"audio_url": audio_url},
                    headers={"authorization": ASSEMBLYAI_API_KEY}
                )
                transcript_id = transcript_response.json()["id"]

                while True:
                    polling = requests.get(
                        f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                        headers={"authorization": ASSEMBLYAI_API_KEY}
                    ).json()
                    if polling["status"] == "completed":
                        break
                    elif polling["status"] == "error":
                        print(f"Error transcribing {filename}: {polling.get('error')}")
                        break
                    time.sleep(5)

                text = polling.get("text", "")

                cur.execute(
                    "INSERT INTO transcriptions (filename, transcript_id, audio_url, text, topic) VALUES (%s, %s, %s, %s, %s)",
                    (filename, transcript_id, audio_url, text, topic)
                )
                conn.commit()

                embedding = model.encode([text])[0]
                index.add(embedding.reshape(1, -1))
                id_mapping[index.ntotal - 1] = filename

                print(f"✅ {filename} processed and indexed under topic '{topic}'")

    faiss.write_index(index, index_file)
    with open(mapping_file, "wb") as f:
        pickle.dump(id_mapping, f)

    print("✅ All transcripts processed and indexed.")

# ------------------ Single File Transcription ------------------
def transcribe_file(audio_path, topic):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"{audio_path} does not exist.")

    filename = os.path.basename(audio_path)

    with open(audio_path, 'rb') as f:
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"authorization": ASSEMBLYAI_API_KEY},
            files={"file": f}
        )
    if response.status_code != 200:
        raise Exception("Upload failed:", response.status_code, response.text)

    audio_url = response.json()["upload_url"]

    transcript_response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json={"audio_url": audio_url},
        headers={"authorization": ASSEMBLYAI_API_KEY}
    )
    transcript_id = transcript_response.json()["id"]

    while True:
        polling = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers={"authorization": ASSEMBLYAI_API_KEY}
        ).json()

        if polling["status"] == "completed":
            break
        elif polling["status"] == "error":
            raise Exception(f"Transcription error: {polling.get('error')}")
        time.sleep(5)

    text = polling.get("text", "")

    cur.execute(
        """
        INSERT INTO transcriptions (filename, transcript_id, audio_url, text, topic)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (filename, transcript_id, audio_url, text, topic)
    )
    conn.commit()

    embedding = model.encode([text])[0]

    index_file = "models/faiss.index"
    mapping_file = "models/id_mapping.pkl"

    if os.path.exists(index_file):
        index = faiss.read_index(index_file)
        with open(mapping_file, "rb") as f:
            id_mapping = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(384)
        id_mapping = {}

    index.add(embedding.reshape(1, -1))
    id_mapping[index.ntotal - 1] = filename

    faiss.write_index(index, index_file)
    with open(mapping_file, "wb") as f:
        pickle.dump(id_mapping, f)

    print(f"✅ '{filename}' transcribed and indexed under topic '{topic}'")

# ------------------ Utility ------------------
def fetch_topics_from_db():
    cur.execute("SELECT DISTINCT topic FROM transcriptions WHERE topic IS NOT NULL")
    return [row[0] for row in cur.fetchall()]

def insert_topic_to_db(filename, topic):
    cur.execute("UPDATE transcriptions SET topic = %s WHERE filename = %s", (topic, filename))
    conn.commit()

# ------------------ Main ------------------
if __name__ == "__main__":
    transcribe_and_index()
