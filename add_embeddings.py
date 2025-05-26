import json
import os
import openai
import time

# Load OpenAI API key from environment variable
openai.api_key = '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'
INPUT_FILE = 'QA_JSON'
OUTPUT_FILE = 'QA_JSON_with_embeddings.json'
EMBEDDING_MODEL = 'text-embedding-ada-002'

# Helper to get embedding from OpenAI

def get_embedding(text, model=EMBEDDING_MODEL, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = openai.embeddings.create(input=[text], model=model)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}. Retrying ({attempt+1}/{max_retries})...")
            time.sleep(2)
    raise RuntimeError(f"Failed to get embedding after {max_retries} attempts.")

# Load the JSON data
with open(INPUT_FILE, 'r') as f:
    data = json.load(f)

# Add embeddings to each item
for category, items in data.items():
    for item in items:
        question = item.get('question', '')
        if question:
            embedding = get_embedding(question)
            item['embedding'] = embedding
        else:
            item['embedding'] = None

# Save the new JSON
with open(OUTPUT_FILE, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Embeddings added and saved to {OUTPUT_FILE}") 