import psycopg2
import requests
import time
import os

# Path to audio_files folder from inside scripts folder
AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_files")

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS transcriptions (
    id SERIAL PRIMARY KEY,
    transcript_id TEXT UNIQUE NOT NULL,
    audio_url TEXT,
    text TEXT,
    filename TEXT UNIQUE
)
""")
conn.commit()

# Upload and transcribe each audio file
for filename in os.listdir(AUDIO_FOLDER):
    if filename.endswith(".mp3"):
        filepath = os.path.join(AUDIO_FOLDER, filename)
        print(f"\nProcessing {filename}...")

        # Check if this filename already exists in DB to avoid duplicate
        cur.execute("SELECT 1 FROM transcriptions WHERE filename = %s", (filename,))
        if cur.fetchone():
            print(f"{filename} already exists in DB. Skipping...")
            continue

        # Upload audio to AssemblyAI
        try:
            with open(filepath, "rb") as f:
                response = requests.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"},
                    files={"file": f}
                )
            response.raise_for_status()
            upload_url = response.json().get("upload_url")
        except Exception as e:
            print(f"Upload failed for {filename}: {e}")
            continue

        if not upload_url:
            print(f"Upload URL missing for {filename}. Skipping...")
            continue

        # Send to transcription
        try:
            transcript_response = requests.post(
                "https://api.assemblyai.com/v2/transcript",
                json={"audio_url": upload_url},
                headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
            )
            transcript_response.raise_for_status()
            transcript_id = transcript_response.json().get("id")
        except Exception as e:
            print(f"Transcription request failed for {filename}: {e}")
            continue

        if not transcript_id:
            print(f"Transcript ID missing for {filename}. Skipping...")
            continue

        # Wait until transcription is complete
        while True:
            poll = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
            ).json()
            if poll["status"] == "completed":
                text = poll.get("text")
                break
            elif poll["status"] == "error":
                print(f"Transcription failed for {filename}. Error: {poll.get('error')}")
                text = None
                break
            time.sleep(3)

        # Only insert if transcription succeeded and text is present
        if transcript_id and upload_url and text:
            # Insert into DB
            try:
                cur.execute("""
                    INSERT INTO transcriptions (transcript_id, audio_url, text, filename)
                    VALUES (%s, %s, %s, %s)
                """, (transcript_id, upload_url, text, filename))
                conn.commit()
                print(f"{filename} transcribed and stored.")
            except psycopg2.Error as e:
                conn.rollback()
                print(f"Failed to insert {filename}: {e}")
        else:
            print(f"No text returned for {filename}. Skipping...")

# Close DB connections
cur.close()
conn.close()
