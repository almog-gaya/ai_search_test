import streamlit as st
import json
import openai
import numpy as np
import os
import http.client
import urllib.request

# Initialize OpenAI client properly
api_key = os.getenv('OPENAI_API_KEY') or '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'

# Use the global API key method instead of client
openai.api_key = api_key

# Disable proxies in the global environment to prevent issues
# This is a workaround for the 'proxies' error in OpenAI client
proxy_env_vars = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
]
saved_env = {}

# Save and remove proxy environment variables
for var in proxy_env_vars:
    if var in os.environ:
        saved_env[var] = os.environ[var]
        del os.environ[var]

if not api_key:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

EMBEDDING_MODEL = 'text-embedding-ada-002'
DATA_FILE = 'QA_json2_with_embeddings.json'
BASE_PROMPT = """
    You are a real estate professional's assistant, chatting via SMS. Reply conversationally but briefly (under 20 words - less if possible). Your main goal is to gather property details (address, price, and sometimes condition) in a natural, friendly manner while making sure the conversation and its history makes sense altogether, and the context is clear.
    
    MOST IMPORTANT RULE: Always prioritize common sense and natural conversation over using knowledge base answers. If a knowledge base answer seems irrelevant to the current conversation, ignore it completely and respond based on context and conversational flow.
    
    Always prioritize natural conversation over information gathering move the conversation forward naturally even if the user is not providing the information you need.
    
    Respond conversationally as a human would, not with a mechanical list of questions. For example, if they say "yes" to having properties, respond with something like "Great! What kind of property do you have in mind?" or "Awesome! Tell me a bit about it."
    
    Never repeat a question if the user has already answered it, even if they repeat their answer.
    Once you have all the required details (address, price, condition), thank the user and close the conversation. Use language similar to: "Thank you for the details! I'll forward this to my team and someone will be in touch soon." Do not repeat this example verbatim or include multiple closing messages.
    
    Always answer the user's question directly using the best-matching QA entry from the knowledge base. If no good match is found in the knowledge base, rely on general conversational rules rather than forcing an irrelevant answer.
    If the user asks a question, answer it first, then (if needed) request any missing details (address, price, condition).
    
    AUDIENCE TYPE AWARENESS:
    - When speaking to REALTORS: Be professional, use industry terminology, focus on mutual benefits.
    - When speaking to HOMEOWNERS: Be more explanatory, focus on their needs and concerns, avoid jargon.
    
    GENERAL RULES:
    - Be conversational, friendly, and human-like - not robotic or scripted.
    - Acknowledge emotions and respond to social cues from the user.
    - If the user seems frustrated, acknowledge it and adjust your approach.
    - Never assume facts not in evidence. Only reference information the user has actually provided.
    - If the user's intent is unclear, ask a clarifying or open-ended question rather than making assumptions.
    - Only request property details if the user has indicated interest in discussing a property.
    - Never close the conversation unless you have actually received all required details.
    - ALWAYS check the conversation history to avoid repetition or asking for information already provided.
    - When gathering information, do it conversationally - don't just list what you need.
    - NEVER respond with "I couldn't find a relevant answer" or similar phrases that reveal technical limitations.
"""

# --- Custom Fields ---
def get_custom_fields():
    st.sidebar.header('Custom Fields')
    agent_name = st.sidebar.text_input('Agent Name', value=st.session_state.get('agent_name', 'Jeff'))
    company = st.sidebar.text_input('Company', value=st.session_state.get('company', 'Reality Check Estates'))
    region = st.sidebar.text_input('Region', value=st.session_state.get('region', 'New York'))
    
    # Add audience type selection with both options
    audience_type = st.sidebar.selectbox('Audience Type', ['Realtor', 'Homeowner'], index=0)
    
    # Add initial message template based on audience type
    st.sidebar.header('Initial Message Template')
    
    if audience_type == 'Realtor':
        default_initial_message = st.session_state.get('initial_message', 
            f"Hey there! I'm {agent_name} from {company}. I work with investors and was wondering if you might have any off-market properties in {region}?")
    else:  # Homeowner
        default_initial_message = st.session_state.get('initial_message', 
            f"Hi! I'm {agent_name} from {company}. I noticed your property at [ADDRESS] and was wondering if you've ever considered selling?")
    
    initial_message = st.sidebar.text_area('Initial Message', value=default_initial_message, height=100)
    
    st.session_state['agent_name'] = agent_name
    st.session_state['company'] = company
    st.session_state['region'] = region
    st.session_state['audience_type'] = audience_type
    st.session_state['initial_message'] = initial_message
    
    return agent_name, company, region, audience_type, initial_message

# --- Conversation History ---
def get_history():
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    return st.session_state['history']

def add_to_history(role, content):
    st.session_state['history'].append({'role': role, 'content': content})

# --- Data Loading ---
@st.cache_resource
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {"questions": []}

def get_embedding(text, model=EMBEDDING_MODEL):
    try:
        response = openai.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Error getting embeddings: {str(e)}")
        # Return a zero vector with the right dimension (1536 for ada-002)
        return [0.0] * 1536

def cosine_similarity(a, b):
    # Check if either vector is empty
    if not a or not b:
        return 0.0
        
    a = np.array(a)
    b = np.array(b)
    
    # Check if vectors have correct dimensions
    if a.size == 0 or b.size == 0:
        return 0.0
    
    # Check if dimensions match
    if a.shape != b.shape:
        st.error(f"Vector dimensions don't match: {a.shape} vs {b.shape}")
        return 0.0
        
    # Avoid division by zero
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return np.dot(a, b) / (norm_a * norm_b)

def search(query, data, top_k=3, min_similarity=0.75, audience_type=None):
    query_emb = get_embedding(query)
    if not query_emb:
        st.error("Failed to generate embeddings for search query")
        return []
        
    results = []
    
    # Updated to work with the new flat JSON structure
    questions = data.get('questions', [])
    
    for item in questions:
        # Skip internal questions
        if item.get('question', '').strip().upper().startswith('INTERNAL:'):
            continue
            
        # Filter by audience type if specified
        if audience_type:
            item_id = item.get('id', '')
            # Items with DOH_ prefix are for homeowners
            if audience_type.lower() == 'homeowner' and not item_id.startswith('DOH_'):
                continue
            # Items with CBR_, SSR_, or ORR_ prefixes are for realtors
            if audience_type.lower() == 'realtor' and item_id.startswith('DOH_'):
                continue
                
        item_emb = item.get('embedding')
        if item_emb:
            try:
                sim = cosine_similarity(query_emb, item_emb)
                results.append((sim, item))
            except Exception as e:
                st.error(f"Error in similarity calculation: {str(e)}")
    
    if not results:
        return []
        
    results.sort(reverse=True, key=lambda x: x[0])
    
    # Return empty list if no good matches
    if not results or results[0][0] < min_similarity:
        return []
    
    return results[:top_k]

def generate_llm_response(user_input, top_qas, system_prompt, history):
    # Check for simple message that shouldn't use knowledge base
    simple_messages = ["yes", "no", "ok", "sounds good", "call me", "tomorrow", "later", "sure"]
    is_simple_message = any(simple in user_input.lower() for simple in simple_messages) and len(user_input.split()) < 5
    
    # Compose context for the LLM
    context = ""
    
    if top_qas and not is_simple_message:
        context = "Relevant Q&A from our knowledge base:\n"
        for i, (sim, item) in enumerate(top_qas):
            context += f"Q: {item['question']}\nA: {item['answer']}\nSimilarity: {sim:.2f}\n\n"
    else:
        context = """
No exact matches found in the knowledge base. Please provide a helpful, natural response based on the conversation context.
IMPORTANT: Never say you couldn't find an answer or don't know something. Always be helpful and confident.
"""
    
    # Build messages for OpenAI Chat API
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_input})
    messages.append({"role": "user", "content": context})
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "I'm having trouble connecting right now. Please try again in a moment."

# --- Streamlit UI ---
st.title("Real Estate AI Assistant")
st.write("Test the AI assistant with different audience types: Realtor or Homeowner")

agent_name, company, region, audience_type, initial_message = get_custom_fields()
data = load_data()
history = get_history()

# Display initial message button
if st.button("Send Initial Message") and not history:
    add_to_history('assistant', initial_message)
    st.rerun()

# Display conversation history
st.subheader("Conversation")
for msg in history:
    if msg['role'] == 'user':
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Bot:** {msg['content']}")

user_input = st.text_input("Type your message:", "")

if st.button("Send") and user_input:
    add_to_history('user', user_input)
    # Use BASE_PROMPT and append agent/company/region/audience_type
    system_prompt = BASE_PROMPT + f"\nAgent Name: {agent_name}\nCompany: {company}\nRegion: {region}\nAudience Type: {audience_type}"
    query = system_prompt + user_input
    with st.spinner("Searching for the best answer..."):
        top_results = search(query, data, top_k=3, audience_type=audience_type)
        llm_response = generate_llm_response(user_input, top_results, system_prompt, history)
        add_to_history('assistant', llm_response)
        st.rerun() 

