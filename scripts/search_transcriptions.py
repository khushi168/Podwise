import faiss 
import numpy as np
import pickle   
from sentence_transformers import SentenceTransformer

# Load the saved FAISS index from file
index = faiss.read_index("transcriptions.index")

# Load the id-to-text mapping from the pickle file
with open("id_text_map.pkl", "rb") as f:
    id_text_map = pickle.load(f)
    
# Load the same SentenceTransformer model used during embedding generation
model = SentenceTransformer('all-MiniLM-L6-v2')

# Take user input for the search query
query = input("enter your search query: ")

# Generate embedding for the input query
query_embedding = model.encode([query])
query_vector = np.array(query_embedding).astype('float32')

# Perform similarity search in FAISS (return top 3 results)
distance, indices = index.search(query_vector, k=3)

# Print the results, skip invalid indices
print("\nTop matching transcriptions: ")
for idx in indices[0]:
    if idx == -1 or idx not in id_text_map:
        continue  # Skip invalid or missing index
    print("-", id_text_map[idx])
