import psycopg2
import requests
import time
import os

# Path to audio_files directory (containing cluster subfolders)
AUDIO_FOLDER_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_files")

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()
 
# Upload and transcribe files in all subfolders (clusters)
for folder in sorted(os.listdir(AUDIO_FOLDER_ROOT)):
    cluster_path = os.path.join(AUDIO_FOLDER_ROOT, folder)
    if not os.path.isdir(cluster_path):
        continue  # Skip files, only process folders

    topic = folder.replace("_", " ").replace("cluster", "").strip()

    for filename in sorted(os.listdir(cluster_path)):
        if filename.endswith(".mp3"):
            filepath = os.path.join(cluster_path, filename)
            print(f"\n📂 Processing {filename} in topic '{topic}'")

            # Upload to AssemblyAI
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
                print(f"❌ Upload failed for {filename}: {e}")
                continue

            if not upload_url:
                print(f"⚠️ No upload URL for {filename}. Skipping...")
                continue

            # Request transcription
            try:
                transcript_response = requests.post(
                    "https://api.assemblyai.com/v2/transcript",
                    json={"audio_url": upload_url},
                    headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
                )
                transcript_response.raise_for_status()
                transcript_id = transcript_response.json().get("id")
            except Exception as e:
                print(f"❌ Transcription request failed for {filename}: {e}")
                continue

            if not transcript_id:
                print(f"⚠️ No transcript ID for {filename}. Skipping...")
                continue

            # Wait for transcription to complete
            while True:
                poll = requests.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
                ).json()

                if poll["status"] == "completed":
                    text = poll.get("text")
                    break
                elif poll["status"] == "error":
                    print(f"❌ Transcription failed for {filename}: {poll.get('error')}")
                    text = None
                    break
                time.sleep(3)

            # Insert into DB if successful
            if transcript_id and upload_url and text:
                try:
                    cur.execute("""
                        INSERT INTO transcriptions (transcript_id, audio_url, text, filename, topic)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (transcript_id, upload_url, text, filename, topic))
                    conn.commit()
                    print(f"✅ {filename} transcribed and stored.")
                except psycopg2.Error as e:
                    conn.rollback()
                    print(f"❌ Failed to insert {filename}: {e}")
            else:
                print(f"⚠️ Skipped {filename} due to missing data.")

# Close DB connection
cur.close()
conn.close()
print("\n✅ All clusters processed and database updated.")
