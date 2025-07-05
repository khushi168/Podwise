# PODWISE 🎧  
  ![Python](https://img.shields.io/badge/Python-3.10-blue)  
  ![License](https://img.shields.io/badge/License-MIT-green)  
  ![Last Updated](https://img.shields.io/badge/Last_Updated-July_2025-orange)  
  ![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**Podwise** is an end-to-end Podcast ETL (Extract, Transform, Load) pipeline that transforms `.mp3` podcast files into **searchable, clustered transcriptions** using:

- 🧠 AssemblyAI for transcription  
- 🗃️ PostgreSQL for storage  
- 🔍 SentenceTransformers + FAISS for semantic vector search  

---

## 🔥 Features

- 🎙️ Converts podcast audio into clean transcripts using AssemblyAI  
- 🧾 Stores transcriptions along with topic tags and filenames in PostgreSQL  
- 🧠 Generates semantic vector embeddings for deep searchability  
- 🔍 Searches podcasts via natural language queries with FAISS  
- 🗂️ Organized by **topic clusters** for scalable search  

---

## 🛠️ Tech Stack

- **Language**: Python 3.10
- **Libraries**:
  - `psycopg2-binary`
  - `sentence-transformers`
  - `faiss-cpu`
  - `numpy`
  - `pickle-mixin`
- **Database**: PostgreSQL 16+
- **Transcription API**: [AssemblyAI](https://www.assemblyai.com/)  

---

## 📁 Project Structure

    podcast_etl_project/
    ├── audio_files/ # Raw .mp3 podcast files
    ├── clustered_topics/ # Organized audio by topic clusters
    ├── models/ # FAISS index + ID mappings
    │ ├── transcriptions.index
    │ ├── faiss_index_id_map.pkl
    │ └── id_text_map.pkl
    ├── scripts/ # Main ETL scripts
    │ ├── fetch_transcriptions.py # Transcribes & stores in DB
    │ ├── generate_embeddings.py # Embeds + indexes transcripts
    │ └── search_transcriptions.py # Searches semantically
    ├── main.py # Pipeline orchestrator (optional)
    ├── requirements.txt
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

---

### Step 6: Push your changes to GitHub after setting up the .gitignore, requirements.txt, etc.

'''bash
      git add .
      git commit -m "Update ETL pipeline with topic clustering and semantic search improvements"
      git push origin master


✅ You can now copy and paste this updated markdown into your `README.md` file in VS Code.
