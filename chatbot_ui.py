import streamlit as st
import json
import openai
import numpy as np
import os

openai.api_key = os.getenv('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') or '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'
EMBEDDING_MODEL = 'text-embedding-ada-002'
DATA_FILE = 'QA_JSON_with_embeddings.json'

@st.cache_resource
def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def get_embedding(text, model=EMBEDDING_MODEL):
    response = openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query, data, top_k=1):
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

# Streamlit UI
st.title("QA Chatbot Demo")
st.write("Ask a question and get an answer from your knowledge base!")

data = load_data()
user_input = st.text_input("You:", "")

if user_input:
    with st.spinner("Searching for the best answer..."):
        top_results = search(user_input, data, top_k=1)
        if top_results:
            sim, category, item = top_results[0]
            st.markdown(f"**Bot:** {item['answer']}")
            st.caption(f"Matched Q: {item['question']} (Category: {category}, Score: {sim:.3f})")
        else:
            st.markdown("**Bot:** Sorry, I couldn't find a relevant answer.") 