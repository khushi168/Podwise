# PODWISE 🎧  
![Python](https://img.shields.io/badge/Python-3.10-blue)  
![License](https://img.shields.io/badge/License-MIT-green)  
![Last Updated](https://img.shields.io/badge/Last_Updated-July_2025-orange)  
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**Podwise** is an end-to-end Podcast ETL (Extract, Transform, Load) pipeline that transforms `.mp3` podcast files into **searchable, clustered transcriptions** using:

- 🧠 AssemblyAI for transcription  
- 🗃️ PostgreSQL for storage  
- 🔍 SentenceTransformers + FAISS for semantic vector search  
- 🌐 Streamlit frontend with secure login/signup system  

---

## 🔥 Features

- 🎙️ Converts podcast audio into clean transcripts using AssemblyAI  
- 🧾 Stores transcriptions along with topic tags and filenames in PostgreSQL  
- 🧠 Generates semantic vector embeddings for deep searchability  
- 🔍 Searches podcasts via natural language queries with FAISS  
- 🗂️ Organized by **topic clusters**, with support for **adding new topics**  
- ⬆️ Upload podcasts directly from the browser  
- 🔐 Seamless **Login / Signup** using `bcrypt` and `users.json`  
- 🎯 Two-part frontend: **Search section** and **Upload section**  
- 🔄 Topic dropdowns dynamically update with newly added topics  

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Libraries**:
  - `streamlit`
  - `bcrypt`
  - `requests`
  - `psycopg2-binary`
  - `sentence-transformers`
  - `faiss-cpu`
  - `numpy`
  - `pickle-mixin`
- **Database**: PostgreSQL 16+
- **Transcription API**: [AssemblyAI](https://www.assemblyai.com/) 

---

## 📁 Project Structure

    Podwise/
      │
      ├── audio_files/                        # All uploaded podcast .mp3 files, grouped by topic
      │   ├── AI_cluster/
      │   ├── Digital_Detox_cluster/
      │   ├── Healthy_eating_cluster/
      │   ├── Importance_of_sleep_cluster/
      │   ├── Mindfulness_cluster/
      │   ├── Personal_Finance_cluster/
      │   ├── Travelling_cluster/
      │   └── temp_audio.mp3
      │
      ├── models/                             # FAISS index and ID mappings
      │   ├── faiss.index
      │   ├── faiss_index_id_map.pkl
      │   ├── id_mapping.pkl
      │   ├── id_text_map.pkl
      │   ├── id_text_map.pkl
      │   └── transcriptions.index
      │
      ├── scripts/                            # Core ETL and backend scripts
      │   ├── fetch_transcriptions.py           # Transcribes audio and inserts into DB
      │   ├── generate_embeddings.py            # Embeds transcriptions and saves to FAISS
      │   ├── search_api.py                     # API to perform semantic search
      │   └── search_transcriptions.py          # Query FAISS index
      │
      ├── transcripts/                        # Optional raw text dump (if needed)
      │
      ├── .env                                # API Keys and secrets
      ├── app.py                              # Entry point if needed
      ├── frontend.py                         # Main Streamlit app file
      ├── main.py                             # Optional additional app logic
      ├── users.json                          # User authentication data
      ├── requirements.txt                    # Python dependencies
      ├── README.md                           # Project documentation
      ├── LICENSE                             # MIT License
      └── podwise_backup.dump                 # PostgreSQL DB backup

---

## 🚀 Getting Started

### 1️⃣ Clone the repository

'''bash
      git clone https://github.com/khushi168/Podwise.git
      cd Podwise


### 2. Create and activate virtual environment
    python -m venv venv
    venv\Scripts\activate      # For Windows

    python3 -m venv venv
    source venv/bin/activate   #For Linux

    python3 -m venv venv
    source venv/bin/activate   #For macOS


### 3. Install project dependencies
    pip install -r requirements.txt


### 4. Setup PostgreSQL
  ## Create a new DB: podcast_etl
  ## Then, create table:

    CREATE TABLE transcriptions (
        id SERIAL PRIMARY KEY,
        audio_url TEXT,
        text TEXT,
        transcript_id TEXT,
        filename TEXT,
        topic TEXT
      );


### 5. Run the Backend pipeline
   ## Step 1: Transcribe and insert into DB
       # Skips previously added files to avoid duplication
       # Adds topic & filename tags automatically
    python scripts/fetch_transcriptions.py

   ## Step 2: Generate embeddings
       # Generates normalized vector embeddings
       # Stores them in FAISS index with ID mappings
    python scripts/generate_embeddings.py

   ## Step 3: Search semantically
       # Query using natural language
       # Retrieves top 1–2 most relevant podcast transcripts
       # Displays filename, topic, match score, and preview
     python scripts/search_transcriptions.py

   ## Step 4: Search locally using CLI
    python scripts/search_api.py

   ## Step 5: Launch Streamlit App (Login + Upload + Search)
    streamlit run frontend.py
    
### Once logged in or signed up, it redirects to frontend.py, where you can:

  1. Use the Search section to:

    Select a topic from dropdown
    
    Enter a question or phrase to query related transcriptions

  2. Use the Upload section to:

    Choose existing topic or enter a new one
    
    Upload a new .mp3 file (saved under audio_files/{topic}_cluster/)

    It gets transcribed and saved directly to the DB

### step 7: users.json Format (auto-generated)
    {
      "users": [
        {
          "username": "khushi",
          "password": "$2b$12$..."
        }
      ]
    }

### step 8: Sample Git Commands
    # Stage all changes
    git add .
    
    # Commit
    git commit -m "Refactor upload & search into frontend.py, support topic creation"
    
    # Push to GitHub
    git push origin main

### Technologies & Concepts Used: 
 ## Data & ETL Pipeline
    ETL (Extract, Transform, Load)
      Extract: Audio files uploaded by users
      Transform: Transcription (AssemblyAI), Embedding (Sentence Transformers)
      Load: Transcriptions stored in PostgreSQL and FAISS

    Audio File Management: .mp3 file handling and topic-wise storage

    File System Organization: Topic-based folder clustering

 ## Natural Language Processing (NLP)
    Automatic Speech Recognition (ASR): "AssemblyAI API"
    Text Embedding: "sentence-transformers"
    Semantic Search: Cosine similarity via FAISS

 ## Backend & Storage
    PostgreSQL: For storing transcriptions, topics, and metadata
    SQLAlchemy: ORM for database interaction
    FAISS (Facebook AI Similarity Search): For fast vector similarity search
    Pickle: Used for ID and text mapping storage

 ## Authentication
    User Management: JSON-based (users.json)
    Password Hashing: "bcrypt"

 ## Frontend
    Streamlit: Main frontend interface (Login, Upload, Search UI)
    Dropdowns & Forms: For topic selection and search queries
    Streamlit Cloud: For potential deployment

 ## Other Technologies & Tools
    Python: Core language for logic and backend
    .env: Environment variable management for API keys and DB credentials
    FAISS Indexing: For scalable, clustered vector search
    Git: Version control
    AssemblyAI Webhooks (optional): Can be added for real-time callbacks


### Deployment Notes
     Can be deployed on Streamlit Cloud for free.
     You must set up a remote PostgreSQL database (e.g., on Railway, Supabase).
     Store your AssemblyAI key & DB credentials in Streamlit secrets or environment variables.


👤 Author:
Khushi Batra – https://www.linkedin.com/in/khushi-batra-445266229/ (LinkedIn)
For queries, suggestions, or collaboration, feel free to connect!
