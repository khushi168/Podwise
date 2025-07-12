import streamlit as st
import os
import requests

# Replace with your backend Render URL
BACKEND_URL = "https://podwise.onrender.com"

# ---------------------------
# 🔍 Search from Backend
# ---------------------------
def streamlit_search(query, topic=None):
    try:
        payload = {"query": query, "topic": topic} if topic else {"query": query}
        response = requests.post(f"{BACKEND_URL}/search", json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        return results
    except Exception as e:
        st.error("❌ Failed to fetch search results from backend.")
        st.exception(e)
        return []

# ---------------------------
# 🎧 Upload and Transcribe
# ---------------------------
def transcribe_file(filepath, filename, topic):
    try:
        with open(filepath, "rb") as file:
            files = {"file": (filename, file, "audio/mpeg")}
            data = {"topic": topic}
            response = requests.post(f"{BACKEND_URL}/upload", files=files, data=data)
        return response.status_code == 200
    except Exception as e:
        st.error("❌ Upload or transcription failed.")
        st.exception(e)
        return False

# ---------------------------
# 🌐 Frontend App
# ---------------------------
def run_podwise_frontend():
    if not st.session_state.get("authenticated"):
        st.error("You must log in first.")
        st.stop()

    st.set_page_config(page_title="Podwise Semantic Search", layout="centered")

    st.sidebar.success(f"Logged in as: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["user"] = ""
        st.rerun()

    st.title("🎙️ PODWISE - Podcast Semantic Search")
    st.write("Search across transcribed podcast episodes using natural language.")

    default_topics = ["AI", "Importance of sleep"]
    extended_topics = ["Digital detox", "Healthy eating", "Personal finance tips"]
    show_all = st.checkbox("🔽 Show more topics")
    topics = default_topics + extended_topics if show_all else default_topics

    # ---------------------------
    # 🔍 SEARCH SECTION
    # ---------------------------
    search_topic = st.selectbox("📂 (Optional) Select a topic:", ["🔽 Select a topic..."] + topics, index=0)
    query = st.text_input("🔍 Enter your query:", placeholder="e.g., What are the benefits of deep sleep?")

    if st.button("Search") and query.strip():
        try:
            topic_param = search_topic if search_topic != "🔽 Select a topic..." else None
            results = streamlit_search(query, topic_param)

            if results:
                top = results[0]
                st.success("✅ Match Found!")
                st.markdown(f"**📜 Transcription Snippet:** {top['text']}")
                st.markdown(f"**📁 Filename:** `{top['filename']}`")
                st.markdown(f"**🗂️ Topic:** `{top['topic']}`")
                st.markdown(f"**📈 Score:** `{round(top['score'], 2)}`")

                audio_url = f"{BACKEND_URL}/audio/{top['topic'].replace(' ', '_')}_cluster/{top['filename']}"
                st.audio(audio_url, format="audio/mp3")
            else:
                st.warning("🫥 No meaningful match found. Try rephrasing?")
        except Exception as e:
            st.exception(e)

    st.markdown("---")

    # ---------------------------
    # 📤 UPLOAD SECTION
    # ---------------------------
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
                        temp_dir = "temp_upload"
                        os.makedirs(temp_dir, exist_ok=True)
                        save_path = os.path.join(temp_dir, uploaded_file.name)

                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.read())

                        success = transcribe_file(save_path, uploaded_file.name, topic_to_use)
                        os.remove(save_path)  # Clean up file after use

                        if success:
                            st.success("✅ File uploaded and transcribed successfully!")
                        else:
                            st.error("❌ Upload succeeded, but transcription failed.")
            except Exception as e:
                st.exception(e)
        else:
            st.warning("⚠️ Please select a file to upload.")
