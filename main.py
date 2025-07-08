import os
import requests
import time
import psycopg2

API_Key = 'b54d78abb6754c60a6d2be277ae1308a'
headers = {'authorization': API_Key}
upload_url = 'https://api.assemblyai.com/v2/upload'
transcript_url = 'https://api.assemblyai.com/v2/transcript'

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)
cur = conn.cursor()

# Path to folder containing .mp3 files (and/or subfolders)
root_folder = "audio_files"

# Loop through all subfolders and files
for subdir, _, files in os.walk(root_folder):
    for file in files:
        if file.endswith(".mp3"):
            file_path = os.path.join(subdir, file)
            print(f"\n🔼 Uploading: {file_path}")

            # Upload audio to AssemblyAI
            with open(file_path, 'rb') as f:
                response = requests.post(upload_url, headers=headers, files={'file': f})
                audio_url = response.json().get('upload_url')

            print(f"✅ Uploaded. URL: {audio_url}")

            # Request transcription
            response = requests.post(transcript_url, json={'audio_url': audio_url}, headers=headers)
            transcript_id = response.json().get('id')

            print(f"📝 Transcription requested. ID: {transcript_id}")

            # Check transcription status
            status_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            print("⏳ Transcription in progress...", end='', flush=True)

            while True:
                response = requests.get(status_url, headers=headers)
                status = response.json()['status']

                if status == 'completed':
                    text = response.json()['text']
                    print("\n✅ Transcription completed.")
                    print(f"🧠 Text: {text[:100]}...")  # Preview first 100 chars

                    # Insert transcription into database
                    cur.execute(
                        "INSERT INTO transcriptions (transcript_id, audio_url, text) VALUES (%s, %s, %s)", 
                        (transcript_id, audio_url, text)
                    )
                    conn.commit()
                    print("💾 Saved to PostgreSQL.")
                    break

                elif status == 'failed':
                    print("\n❌ Transcription failed.")
                    break

                else:
                    time.sleep(3)

# Close DB connection
cur.close()
conn.close()
print("\n✅ All files processed and saved to database.")
