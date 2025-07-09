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
- 🗂️ Organized by **topic clusters** for scalable search  
- 🧩 Upload and transcribe new `.mp3` files via browser  
- 🔐 Seamless **Login / Signup** system using `bcrypt` and `users.json`  
- 🧠 Option to show more/less topics dynamically for quick access  

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
    ├── audio_files/                # All uploaded podcast .mp3 files, grouped by topic
    │   └── AI_cluster/
    │   └── Sleep_cluster/
    ├── models/                     # FAISS index and ID mappings
    │   ├── transcriptions.index
    │   ├── faiss_index_id_map.pkl
    │   └── id_text_map.pkl
    ├── scripts/                    # Core ETL and backend scripts
    │   ├── fetch_transcriptions.py   # Uses AssemblyAI to transcribe audio and insert into DB
    │   ├── generate_embeddings.py    # Converts transcripts into vector embeddings + FAISS
    │   └── search_api.py             # Backend API for semantic search
    ├── auth_app.py                 # Streamlit login/signup with bcrypt
    ├── frontend.py                 # Main Streamlit frontend (search + upload)
    ├── users.json                  # Auto-generated user DB with hashed passwords
    ├── requirements.txt            # Python dependencies
    ├── .gitignore
    └── README.md

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


### 5. Run the pipeline
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

---

### Step 6: Start the Login + Frontend App

    streamlit run auth_app.py
    
✅ Once logged in or signed up, it redirects to frontend.py, where you can:

  # Upload new .mp3 files under a topic
  # Search across podcast content using natural language  
  # Listen to the results in-browser 
  # Dynamically explore topic clusters with “Show more topics” toggle

### step 7: users.json Format (auto-generated)
    {
      "users": [
        {
          "username": "khushi",
          "password": "$2b$12$..."
        }
      ]
    }

### step 8: ✅ Sample Git Commands
    # Stage all changes
    git add .
    
    # Commit
    git commit -m "Add login/signup with bcrypt and integrate frontend redirection"
    
    # Push to GitHub
    git push origin main


👤 Author:
Khushi Batra – https://www.linkedin.com/in/khushi-batra-445266229/ (LinkedIn)
For queries, suggestions, or collaboration, feel free to connect!
