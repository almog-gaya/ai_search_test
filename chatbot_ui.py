import streamlit as st
import json
import openai
import numpy as np
import os

openai.api_key = os.getenv('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') or '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'
EMBEDDING_MODEL = 'text-embedding-ada-002'
DATA_FILE = 'QA_JSON_with_embeddings.json'
BASE_PROMPT = """
You are a helpful, concise, and professional real estate assistant. 
- NEVER ask for details (address, price, condition) already provided in the conversation.
- If unsure, acknowledge existing details and move forward.
- Your role: Engage real estate agents and homeowners in business-focused, ongoing conversations to find off-market or creative deals.
- Objective: Build trust, gather key property details, and position yourself as a valuable partner.
- Use natural, text-friendly language (contractions, simple words, no formalities).
- STRICT: Max 20 words per response, one clear point, no explanations unless asked, always advance the conversation.
- NEVER use forbidden words: 'traditional payment terms', urgency words, approval words, financing methods.
- Use only approved phrases: 'traditional purchase', 'conventional financing', 'standard payment', 'efficient process', 'reliable'.
- Mirror user's style and energy, keep it casual professional, avoid robotic or overly formal language.
- If user mentions forbidden words, rephrase using approved alternatives.
- Respond naturally to real estate terms (ROI, CAP, 1031, double close, etc.).
"""

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

def search(query, data, top_k=1, min_similarity=0.7):
    query_emb = get_embedding(query)
    results = []
    for category, items in data.items():
        for item in items:
            # Filter out internal/instructional Q&A
            if item.get('question', '').strip().upper().startswith('INTERNAL:'):
                continue
            item_emb = item.get('embedding')
            if item_emb:
                sim = cosine_similarity(query_emb, item_emb)
                results.append((sim, category, item))
    results.sort(reverse=True, key=lambda x: x[0])
    # Fallback if best match is below threshold
    if results and results[0][0] < min_similarity:
        return []
    return results[:top_k]

def generate_llm_response(user_input, top_qas, base_prompt):
    # Compose context for the LLM
    context = "Relevant Q&A from our knowledge base:\n"
    for i, (sim, category, item) in enumerate(top_qas):
        context += f"Q: {item['question']}\nA: {item['answer']}\n"
    context += f"\nUser: {user_input}\nBot:"

    # Call OpenAI Chat API (gpt-3.5-turbo)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": context}
        ],
        max_tokens=100,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

# Streamlit UI
st.title("QA Chatbot Demo")
st.write("Ask a question and get an answer from your knowledge base!")

data = load_data()
user_input = st.text_input("You:", "")

if user_input:
    query = BASE_PROMPT + user_input
    with st.spinner("Searching for the best answer..."):
        top_results = search(query, data, top_k=3)
        if top_results:
            llm_response = generate_llm_response(user_input, top_results, BASE_PROMPT)
            st.markdown(f"**Bot:** {llm_response}")
            sim, category, item = top_results[0]
            st.caption(f"Matched Q: {item['question']} (Category: {category}, Score: {sim:.3f})")
        else:
            st.markdown("**Bot:** Sorry, I couldn't find a relevant answer.") 