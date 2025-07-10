import streamlit as st
import os
import pickle
import time
import faiss
import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer
import requests

ASSEMBLYAI_API_KEY = "b54d78abb6754c60a6d2be277ae1308a"

# --- Utility Functions ---
def streamlit_search(query: str, topic: str = None):
    models_dir = os.path.join(os.path.dirname(__file__), "models")
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

def transcribe_file(filepath, filename, topic):
    headers = {"authorization": ASSEMBLYAI_API_KEY}

    with open(filepath, "rb") as f:
        upload_res = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, files={"file": f})
    upload_res.raise_for_status()
    upload_url = upload_res.json()["upload_url"]

    transcript_res = requests.post("https://api.assemblyai.com/v2/transcript", json={"audio_url": upload_url}, headers=headers)
    transcript_res.raise_for_status()
    transcript_id = transcript_res.json()["id"]

    while True:
        poll_res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        poll_json = poll_res.json()
        if poll_json["status"] == "completed":
            transcript_text = poll_json["text"]
            break
        elif poll_json["status"] == "error":
            raise Exception(poll_json["error"])
        time.sleep(3)

    conn = psycopg2.connect(host="localhost", database="podcast_etl", user="postgres", password="160803")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transcriptions (transcript_id, audio_url, text, filename, topic)
        VALUES (%s, %s, %s, %s, %s)
    """, (transcript_id, upload_url, transcript_text, filename, topic))
    conn.commit()
    cur.close()
    conn.close()

    return "Transcription and insertion successful"

# --- Run Streamlit UI ---
def run_podwise_frontend():
    if not st.session_state.get("authenticated"):
        st.error("You must log in first.")
        st.stop()

    st.sidebar.success(f"Logged in as: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["user"] = ""
        st.rerun()

    st.set_page_config(page_title="Podwise Semantic Search", layout="centered")
    st.title("🎙️ PODWISE - Podcast Semantic Search")
    st.write("Search across transcribed podcast episodes using natural language.")

    default_topics = ["AI", "Importance of sleep"]
    extended_topics = ["Digital detox", "Healthy eating", "Personal finance tips"]

    show_all = st.checkbox("🔽 Show more topics")
    topics = default_topics + extended_topics if show_all else default_topics

    search_topic = st.selectbox("📂 (Optional) Select a topic:", ["🔽 Select a topic..."] + topics, index=0)
    query = st.text_input("🔍 Enter your query:", placeholder="e.g., What are the benefits of deep sleep?")

    if st.button("Search") and query.strip():
        try:
            topic_param = None if search_topic == "🔽 Select a topic..." else search_topic
            result_list = streamlit_search(query, topic_param)

            if result_list:
                result = result_list[0]
                st.success("✅ Match Found!")
                st.markdown(f"**📜 Transcription Snippet:** {result['text']}")
                st.markdown(f"**📁 Filename:** `{result['filename']}`")
                st.markdown(f"**🗂️ Topic:** `{result['topic']}`")
                st.markdown(f"**📈 Score:** `{round(result['score'], 2)}`")

                audio_file_path = f"audio_files/{result['topic'].replace(' ', '_')}_cluster/{result['filename']}"
                if os.path.exists(audio_file_path):
                    with open(audio_file_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                else:
                    st.error(f"🔇 Audio file not found at: `{audio_file_path}`")
            else:
                st.warning("🫥 No meaningful match found. Try rephrasing?")
        except Exception as e:
            st.exception(e)

    st.markdown("---")
    st.header("📨 Upload New Podcast")

    upload_topics = ["🔽 Select a topic..."] + topics + ["Other"]
    selected_upload_topic = st.selectbox("🗂️ Choose a topic for this podcast:", upload_topics, index=0)

    custom_topic = ""
    if selected_upload_topic == "Other":
        custom_topic = st.text_input("✍️ Enter custom topic name")

    uploaded_file = st.file_uploader("🎧 Choose an MP3 file to upload", type=["mp3"])

    if st.button("Upload & Transcribe"):
        if uploaded_file:
            try:
                if selected_upload_topic == "🔽 Select a topic...":
                    st.warning("⚠️ Please select a topic or enter a custom one.")
                else:
                    topic_to_use = custom_topic.strip() if selected_upload_topic == "Other" else selected_upload_topic
                    if not topic_to_use:
                        st.warning("⚠️ Please enter a custom topic.")
                    else:
                        cluster_folder = f"audio_files/{topic_to_use.replace(' ', '_')}_cluster"
                        os.makedirs(cluster_folder, exist_ok=True)
                        save_path = os.path.join(cluster_folder, uploaded_file.name)

                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.read())

                        try:
                            transcribe_file(save_path, uploaded_file.name, topic_to_use)
                            st.success("✅ File uploaded and transcribed successfully!")
                        except Exception as e:
                            st.error("❌ Upload succeeded, but transcription failed.")
                            st.exception(e)
            except Exception as e:
                st.exception(e)
        else:
            st.warning("⚠️ Please select a file to upload.")
