import streamlit as st
import os
import json
import bcrypt
from dotenv import load_dotenv
load_dotenv()

from scripts.search_api import streamlit_search
from scripts.fetch_transcriptions import transcribe_file, fetch_topics_from_db, insert_topic_to_db

st.set_page_config(page_title="🎙️ Podwise", layout="wide")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- Auth Helpers ---
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file)

# --- Signup/Login Functions ---
def signup():
    st.subheader("🔐 Sign Up")
    new_user = st.text_input("👤 Username", key="signup_user")
    new_password = st.text_input("🔑 Password", type="password", key="signup_pass")
    if st.button("📝 Create Account"):
        users = load_users()
        if new_user in users:
            st.warning("⚠️ Username already exists.")
        else:
            hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            users[new_user] = hashed_pw
            save_users(users)
            st.success("✅ Account created! You can now log in.")

def login():
    st.subheader("🔐 Login")
    user = st.text_input("👤 Username", key="login_user")
    password = st.text_input("🔑 Password", type="password", key="login_pass")
    if st.button("Let's go"):
        users = load_users()
        if user in users and bcrypt.checkpw(password.encode(), users[user].encode()):
            st.session_state.logged_in = True
            st.session_state.username = user
            st.success("✅ Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("🚫 Invalid username or password.")

# --- Auth Tabs ---
if not st.session_state.logged_in:
    login_tab, signup_tab = st.tabs(["🔓 Login", "🆕 Sign Up"])
    with login_tab:
        login()
    with signup_tab:
        signup()

# --- Main Interface ---
if st.session_state.logged_in:
    with st.sidebar:
        st.write(f"👤 Logged in as: `{st.session_state.username}`")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🎙️ Podwise: Podcast Semantic Search")

    # --- Search Section ---
    st.markdown("## 🔍 Search Podcasts")
    topics = fetch_topics_from_db()
    selected_topic = st.selectbox("🎯 Select Topic", ["Select here"] + topics, key="search_topic")
    query = st.text_input("💬 Ask your question:", key="search_query")

    if st.button("🧠 Search"):
        if query and selected_topic != "Select here":
            result = streamlit_search(query, selected_topic)
            if "error" in result:
                st.error("🚫 " + result["error"])
            else:
                st.toast("✅ Result found!")
                st.markdown(f"**📌 Topic:** `{result.get('topic', 'N/A')}`")
                st.markdown(f"**🎧 Filename:** `{result.get('filename', 'N/A')}`")
                st.markdown(f"**📝 Transcription:**\n\n{result.get('text', 'No transcript available.')}")
                if result.get("audio_url"):
                    st.markdown("🎵 Download MP3:")
                    st.markdown(f"🔗 [Click here to download audio]({result['audio_url']})")
                txt_data = f"Topic: {result.get('topic', '')}\nFilename: {result.get('filename', '')}\n\nTranscription:\n{result.get('text', '')}"
                st.download_button("📥 Save Transcript (.txt)", data=txt_data, file_name="transcription.txt", mime="text/plain")
        else:
            st.warning("⚠️ Please enter a query and select a topic.")

    st.markdown("---")

    # --- Upload Section ---
    st.markdown("## 🗃️ Upload a Podcast")
    upload_topics = ["Select here"] + topics + ["Other"]
    upload_topic = st.selectbox("🎯 Choose Topic", upload_topics, key="upload_topic")
    new_topic = ""
    if upload_topic == "Other":
        new_topic = st.text_input("✏️ Enter new topic name", key="new_topic_name")

    uploaded_file = st.file_uploader("📁 Upload .mp3 file", type=["mp3"], key="podcast_upload")

    if st.button("🚀 Upload & Transcribe"):
        final_topic = new_topic.strip() if upload_topic == "Other" else upload_topic
        if uploaded_file and final_topic and final_topic != "Select here":
            # Create topic-specific cluster folder
            cluster_folder = os.path.join("audio_files", f"{final_topic}_cluster")
            os.makedirs(cluster_folder, exist_ok=True)

            # Clean filename and save file
            original_filename = uploaded_file.name
            file_path = os.path.join(cluster_folder, original_filename)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            # Insert topic to DB if new
            if upload_topic == "Other" and final_topic not in topics:
                insert_topic_to_db(final_topic, final_topic)

            # Transcribe
            transcribe_file(file_path, final_topic)

            st.success(f"✅ Uploaded and transcribed under topic: `{final_topic}`")
        else:
            st.warning("⚠️ Please upload a file and select or enter a topic.")
