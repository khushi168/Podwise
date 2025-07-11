import os
import time
import requests
import streamlit as st

# Replace with your actual backend URL
BACKEND_URL = "https://podwise.onrender.com"

# Get API Key from environment variable
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

def streamlit_search(query: str, topic: str = None):
    """Send search query to backend API and return results"""
    try:
        payload = {"query": query}
        if topic:
            payload["topic"] = topic
        res = requests.post(f"{BACKEND_URL}/search", json=payload)
        res.raise_for_status()
        return res.json().get("results", [])
    except Exception as e:
        st.error("❌ Failed to fetch search results from backend.")
        raise e

def transcribe_file(filepath, filename, topic):
    """Upload MP3 and trigger transcription using backend API"""
    try:
        with open(filepath, "rb") as f:
            files = {'file': (filename, f, 'audio/mpeg')}
            data = {'topic': topic}
            headers = {"Authorization": ASSEMBLYAI_API_KEY}  # optional if needed at frontend
            res = requests.post(f"{BACKEND_URL}/upload", data=data, files=files)
            res.raise_for_status()
            return True
    except Exception as e:
        st.error("❌ Upload or transcription failed.")
        raise e
