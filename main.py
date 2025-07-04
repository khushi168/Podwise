import requests
import time   #provides functions related to time and delays
import psycopg2    #to connect & work with PosgtreSQL 

API_Key='b54d78abb6754c60a6d2be277ae1308a' 

upload_url = 'https://api.assemblyai.com/v2/upload'    #endpoint to upload audio files

print()

headers={'authorization':API_Key}    #for API key authentication

filename='short_test.mp3'

#opening audio file in binary mode
with open(filename, 'rb') as f:
    #sending the file to assemblyAI using POST request
    response=requests.post(upload_url, headers=headers, files={'file': f})
    
    #extract the uploaded audio URL from the response JSON
    audio_url=response.json()['upload_url']
    
print("Audio Uploaded:", audio_url)
print()

#endpoint to request a transcription
transcript_url='https://api.assemblyai.com/v2/transcript'

#Prepare JSON data telling AssemblyAI where the uploaded audio is
json_data={'audio_url': audio_url}

#Send transcription request.
response=requests.post(transcript_url, json=json_data, headers=headers)

#get the unique transcription job id
transcript_id=response.json()['id']

print("Transcription requested, ID:", transcript_id)
print()

#URL to check the status of transcription job
status_url=f'https://api.assemblyai.com/v2/transcript/{transcript_id}'

print("Transcription in progress...", end='', flush=True)
print()

while True:
    #get the current status of transcription job
    response=requests.get(status_url, headers=headers)
    
    #get status field from JSON response
    status=response.json()['status']
    if status=='completed':
        print("\nTranscription completed!")
        print()
        print(response.json()['text'])
        break
    elif status=='failed':
        print("\rTranscription failed.")
        break
    else:
        #pauses/sleeps the program for 3 seconds, we use it in the loop so that we don’t spam the API with rapid requests
        time.sleep(3)    
        

#connect to postgreSQL db
conn=psycopg2.connect(
    host="localhost",          #database server location(local machine)
    database="podcast_etl",    #name of the db
    user="postgres",           #username to connect with(change if required)
    password="160803",         #db password
)

cur=conn.cursor()              #create a cursor object to execute SQL commands

#insert transcription data
cur.execute(
    "INSERT INTO transcriptions (transcription_id, audio_url, text) VALUES (%s, %s, %s)",
    
    #provide values for each column
    (transcript_id, audio_url, response.json()['text'])
)

#commit changes and close connection
conn.commit()                   #commit changes to make sure data is saved in db
cur.close()                     #close the cursor
conn.close()                    #close connection to free resources

print("\nTranscription data inserted into PostgreSQL database.")