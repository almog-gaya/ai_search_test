import json
import openai
import numpy as np
import os

openai.api_key = os.getenv('OPENAI_API_KEY') or 'YOUR_OPENAI_API_KEY'
EMBEDDING_MODEL = 'text-embedding-ada-002'
DATA_FILE = 'QA_JSON_with_embeddings.json'

def get_embedding(text, model=EMBEDDING_MODEL):
    response = openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query, data, top_k=3):
    query_emb = get_embedding(query)
    results = []
    for category, items in data.items():
        for item in items:
            item_emb = item.get('embedding')
            if item_emb:
                sim = cosine_similarity(query_emb, item_emb)
                results.append((sim, category, item))
    results.sort(reverse=True, key=lambda x: x[0])
    return results[:top_k]

# Load data
with open(DATA_FILE, 'r') as f:
    data = json.load(f)

# Test query
query = "seller wants to avoid foreclosure"
top_results = search(query, data, top_k=3)
print(f"Top results for query: '{query}'\n")
for sim, category, item in top_results:
    print(f"[{category}] {item['question']} (score: {sim:.3f})")
    print(f"Answer: {item['answer']}\n") 