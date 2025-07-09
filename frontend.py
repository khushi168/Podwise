import streamlit as st
import requests
import os

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
            payload = {"query": query}
            if search_topic != "🔽 Select a topic...":
                payload["topic"] = search_topic

            response = requests.post("http://localhost:5000/search", json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("match_found"):
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
            else:
                st.error("🥴 Backend error.")
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

                        res = requests.post("http://localhost:5000/transcribe", json={
                            "filepath": save_path,
                            "filename": uploaded_file.name,
                            "topic": topic_to_use
                        })

                        if res.status_code == 200:
                            st.success("✅ File uploaded and transcribed successfully!")
                        else:
                            st.error("❌ Upload succeeded, but transcription failed.")
            except Exception as e:
                st.exception(e)
        else:
            st.warning("⚠️ Please select a file to upload.")
