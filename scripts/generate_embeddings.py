import psycopg2

#Imports the transformer model used to convert text into numerical vector embeddings
from sentence_transformers import SentenceTransformer

#high speed vector similarity search library
import faiss 

#to handle numerical data
import numpy as np

#db connection and fetching transcriptions
conn=psycopg2.connect(
    host="localhost",
    database="podcast_etl",
    user="postgres",
    password="160803"
)

#connects to PostgreSQL db (posdcast_etl)
cur=conn.cursor()

#create cursor object to execute SQL commands
cur.execute("SELECT id, text FROM transcriptions")

#executes the query to fetch id and text from table
rows = cur.fetchall()

#close the db and connection after fetching the data
cur.close()
conn.close()

#load pre-trained sentence transformer model for generating semantic embeddings
model=SentenceTransformer('all-MiniLM-L6-v2')

#prepare texts and IDs in two lists
texts=[row[1] for row in rows]
ids=[row[0] for row in rows]

#generate embeddings (vector transcriptions)
embeddings=model.encode(texts)

#convert to numpy array type "float32" (req by: FAISS)
embeddings_np=np.array(embeddings).astype('float32')

#create FAISS index
index = faiss.IndexFlatL2(embeddings_np.shape[1])     #L2 euclidean distance
index.add(embeddings_np)

#save ID-to-text map (for search output)
import pickle

#add all generated embeddings to the FAISS index
with open("id_text_map.pkl", "wb") as f:
    pickle.dump(dict(zip(range(len(ids)), texts)), f)
    
# Save the FAISS index to a file
faiss.write_index(index, "transcriptions.index")
    
print("Embeddings generated and FAISS index created!!")