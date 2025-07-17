import streamlit as st
import os

# 👇 Local script import (no backend URL)
from scripts.search_api import streamlit_search, transcribe_file

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
        topic_param = search_topic if search_topic != "🔽 Select a topic..." else None
        results = streamlit_search(query, topic_param)

        if results:
            top = results[0]
            st.success("✅ Match Found!")
            st.markdown(f"**📜 Transcription Snippet:** {top['text']}") 
            st.markdown(f"**📁 Filename:** `{top['filename']}`")
            st.markdown(f"**🗂️ Topic:** `{top['topic']}`")
            st.markdown(f"**📈 Score:** `{round(top['score'], 2)}`")

            # 🔊 Play local audio file
            audio_path = os.path.join("audio_files", top['topic'], top['filename'])
            if os.path.exists(audio_path):
                st.audio(audio_path, format="audio/mp3")
            else:
                st.warning("⚠️ Audio file not found locally.")
        else:
            st.warning("🫥 No meaningful match found. Try rephrasing?")

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
                    os.remove(save_path)

                    if success:
                        st.success("✅ File uploaded and transcribed successfully!")
                    else:
                        st.error("❌ Upload succeeded, but transcription failed.")
        else:
            st.warning("⚠️ Please select a file to upload.")
