import streamlit as st
import os
import requests

BACKEND_URL = "https://podwise.onrender.com"

# ---------------------------
# 🔍 Search from Backend
# ---------------------------
def streamlit_search(query, topic=None):
    try:
        payload = {"query": query, "topic": topic} if topic else {"query": query}
        response = requests.post(f"{BACKEND_URL}/search", json=payload)
        return response.json()
    except Exception as e:
        return {"match_found": False, "error": str(e)}

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
        return False

# ---------------------------
# 🌐 Frontend App
# ---------------------------
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
            topic = search_topic if search_topic != "🔽 Select a topic..." else None
            result = streamlit_search(query, topic)

            if result.get("match_found"):
                st.success("✅ Match Found!")
                st.markdown(f"**📜 Transcription Snippet:** {result['text']}")
                st.markdown(f"**📁 Filename:** `{result['filename']}`")
                st.markdown(f"**🗂️ Topic:** `{result['topic']}`")
                st.markdown(f"**📈 Score:** `{round(result['score'], 2)}`")

                audio_url = f"{BACKEND_URL}/audio/{result['topic'].replace(' ', '_')}_cluster/{result['filename']}"
                st.audio(audio_url, format="audio/mp3")
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
                        save_path = os.path.join("temp_upload", uploaded_file.name)
                        os.makedirs("temp_upload", exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.read())

                        success = transcribe_file(save_path, uploaded_file.name, topic_to_use)

                        if success:
                            st.success("✅ File uploaded and transcribed successfully!")
                        else:
                            st.error("❌ Upload succeeded, but transcription failed.")
            except Exception as e:
                st.exception(e)
        else:
            st.warning("⚠️ Please select a file to upload.")
