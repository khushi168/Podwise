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
        continue  # Skip non-folder items

    topic = folder.replace("_", " ").replace("cluster", "").strip()

    for filename in sorted(os.listdir(cluster_path)):
        if filename.endswith(".mp3"):
            filepath = os.path.join(cluster_path, filename)
            print(f"\n📂 Processing {filename} in topic '{topic}'")

            # Upload to AssemblyAI
            try:
                with open(filepath, "rb") as f:
                    upload_res = requests.post(
                        "https://api.assemblyai.com/v2/upload",
                        headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"},
                        files={"file": f}
                    )
                upload_res.raise_for_status()
                upload_url = upload_res.json().get("upload_url")
                print(f"✅ Uploaded. URL: {upload_url}")
            except Exception as e:
                print(f"❌ Upload failed for {filename}: {e}")
                continue

            # Request transcription
            try:
                trans_res = requests.post(
                    "https://api.assemblyai.com/v2/transcript",
                    json={"audio_url": upload_url},
                    headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
                )
                trans_res.raise_for_status()
                transcript_id = trans_res.json().get("id")
                print(f"📝 Transcription requested. ID: {transcript_id}")
            except Exception as e:
                print(f"❌ Transcription request failed for {filename}: {e}")
                continue

            # Poll until complete
            print("⏳ Waiting for transcription to complete...")
            while True:
                poll = requests.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"authorization": "b54d78abb6754c60a6d2be277ae1308a"}
                ).json()

                if poll.get("status") == "completed":
                    text = poll.get("text")
                    print(f"✅ Transcription complete.")
                    break
                elif poll.get("status") == "error":
                    print(f"❌ Transcription failed: {poll.get('error')}")
                    text = None
                    break
                time.sleep(3)

            # Insert into DB (skip if filename exists)
            if transcript_id and upload_url and text:
                try:
                    cur.execute("""
                        INSERT INTO transcriptions (transcript_id, audio_url, text, filename, topic)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (filename) DO NOTHING
                    """, (transcript_id, upload_url, text, filename, topic))
                    conn.commit()
                    print(f"📥 Saved: {filename}")
                except psycopg2.Error as e:
                    conn.rollback()
                    print(f"❌ DB insert failed for {filename}: {e}")
            else:
                print(f"⚠️ Skipped {filename} due to missing data.")

# Close DB connection
cur.close()
conn.close()
print("\n✅ All audio files processed. Database is up to date.")
