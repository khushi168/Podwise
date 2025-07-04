# PODWISE 🎧 
![Python](https://img.shields.io/badge/Python-3.10-blue)  
![License](https://img.shields.io/badge/License-MIT-green)  
![Last Updated](https://img.shields.io/badge/Last_Updated-July_2025-orange)  
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**Podwise** is a Podcast ETL (Extract, Transform, Load) pipeline that converts podcast `.mp3` files into searchable transcriptions using:

- 🧠 AssemblyAI for transcription
- 🗃️ PostgreSQL for storage
- 🔍 FAISS + SentenceTransformers for semantic search

---

## Features

- Automatically extracts audio files and transcribes them.
- Stores transcriptions in a PostgreSQL database.
- Generates semantic vector embeddings.
- Allows natural language search across podcasts.
- Uses FAISS for fast similarity search.

---

## Tech Stack

- **Language**: Python 3.x  
- **Libraries**:
  - `psycopg2-binary`
  - `sentence-transformers`
  - `faiss-cpu`
  - `numpy`
  - `pickle-mixin`
- **Database**: PostgreSQL 16+
- **Transcription API**: [AssemblyAI](https://www.assemblyai.com/)

---

## 📁 Folder Structure
  podcast_etl_project/
  ├── audio_files/ # Raw .mp3 podcast files
  ├── models/ # FAISS index + ID mapping
  ├── scripts/ # ETL scripts
  │ ├── fetch_transcriptions.py
  │ ├── generate_embeddings.py
  │ └── search_transcriptions.py
  ├── main.py # Master orchestrator
  ├── requirements.txt
  ├── .gitignore
  └── README.md

---

## Setup Instructions

### 1. Clone the repository
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
        filename TEXT,
        text TEXT
    );


### 5. Run the pipeline
   ## Step 1: Transcribe and insert into DB
     python scripts/fetch_transcriptions.py

   ## Step 2: Generate embeddings
     python scripts/generate_embeddings.py

   ## Step 3: Search semantically
     python scripts/search_transcriptions.py

---

### Step 6: Push your changes to GitHub after setting up the .gitignore, requirements.txt, etc.

'''bash
      git add .
      git commit -m "Set up project structure and ETL pipeline"
      git push origin master


✅ You can now copy and paste this updated markdown into your `README.md` file in VS Code.
