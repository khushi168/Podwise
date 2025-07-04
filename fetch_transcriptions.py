import psycopg2
import requests
import time
import os

AUDIO_FOLDER = "audio_files"  # relative to scripts folder

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

        #Check if this filename already exists in DB to avoid duplicate
        cur.execute("SELECT 1 FROM transcriptions WHERE filename = %s", (filename,))
        if cur.fetchone():
            print(f"{filename} already exists in DB. Skipping...")
            continue

        # Upload audio to AssemblyAI
        with open(filepath, "rb") as f:
            response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"},
                files={"file": f}
            )
        upload_url = response.json()["upload_url"]   # add filename reference

        # Send to transcription
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            json={"audio_url": upload_url},
            headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
        )
        transcript_id = transcript_response.json()["id"]

        # Wait until transcription is complete
        while True:
            poll = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
            ).json()
            if poll["status"] == "completed":
                text = poll["text"]
                break
            elif poll["status"] == "error":
                print("Transcription failed.")
                text = None
                break
            time.sleep(3)

        #Only insert if transcription succeeded and text is present
        if text:
            # Insert into DB
            cur.execute("""
            INSERT INTO transcriptions (transcript_id, audio_url, text, filename)
            VALUES (%s, %s, %s, %s)
            """, (transcript_id, upload_url, text, filename))
            conn.commit()
            print(f"{filename} transcribed and stored.")
        else:
            print(f"{filename} transcription skipped due to error.")

#Close DB connections
cur.close()
conn.close()
