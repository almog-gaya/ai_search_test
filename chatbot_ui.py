import streamlit as st
import json
import openai
import numpy as np
import os

openai.api_key = os.getenv('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') or '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'
EMBEDDING_MODEL = 'text-embedding-ada-002'
DATA_FILE = 'QA_JSON_with_embeddings.json'
BASE_PROMPT = """
    You are a real estate professional's assistant, chatting via SMS with realtors. Reply conversationally but briefly (under 20 words - less if possible). Your main goal is to gather property details (address, price, and sometimes condition) in a natural, friendly manner while making sure the conversation and its history makes sense altogether, and the context is clear.
    
    MOST IMPORTANT RULE: Always prioritize common sense and natural conversation over using knowledge base answers. If a knowledge base answer seems irrelevant to the current conversation, ignore it completely and respond based on context and conversational flow.
    
    
    Always prioritize natural conversation over information gathering move the conversation forward naturally even if the user is not providing the information you need.
    
    Respond conversationally as a human would, not with a mechanical list of questions. For example, if they say "yes" to having properties, respond with something like "Great! What kind of property do you have in mind?" or "Awesome! Tell me a bit about it."
    
    Never repeat a question if the user has already answered it, even if they repeat their answer.
    Once you have all the required details (address, price, condition), thank the user and close the conversation. Use language similar to: "Thank you for the details! I'll forward this to my team and someone will be in touch soon." Do not repeat this example verbatim or include multiple closing messages.
    
    Always answer the user's question directly using the best-matching QA entry from the knowledge base. If no good match is found in the knowledge base, rely on general conversational rules rather than forcing an irrelevant answer.
    If the user asks a question, answer it first, then (if needed) request any missing details (address, price, condition).
    
    CRITICAL INSTRUCTIONS:
    - When the user asks "what are you looking for" or any variation (including phrases like "sure what are you looking for"), ALWAYS respond with specific property criteria from the knowledge base. The answer should mention your interest in properties needing renovation, off-market deals, etc.
    - Pay close attention to questions hidden in statements that start with words like "sure" or "ok" - these are still questions that need direct answers.
    - Never interpret "what are you looking for" as confirmation that they have a property. It is a question about what types of properties YOU are seeking.
    - For simple, straightforward replies like "ok", "yes", "sounds good", "call me tomorrow", IGNORE any knowledge base matches and respond naturally based on context.
    
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
    audience_type = st.sidebar.selectbox('Audience Type', ['Realtor'], index=0)
    
    # Add property criteria selection
    st.sidebar.header('Property Criteria')
    criteria_options = [
        'Creative Finance (Realtor)',
        'Off Market Deals (Realtor)',
        'Short Sale (Realtor)',
        'Cash Buyer (Realtor)'
    ]
    property_criteria = st.sidebar.selectbox('Property Criteria', criteria_options, index=1)  # Default to Off Market Deals
    
    # Add criteria description based on selection
    criteria_descriptions = {
        'Creative Finance (Realtor)': "Looking for properties where seller might consider creative financing options like seller financing, lease options, or subject-to deals.",
        'Off Market Deals (Realtor)': "Looking for SFH/multiplex needing renovation, off-market. Pocket listings, pre-MLS, motivated sellers.",
        'Short Sale (Realtor)': "Looking for properties where the seller owes more than the property is worth and may be facing foreclosure.",
        'Cash Buyer (Realtor)': "Looking for properties needing work where a fast, as-is cash purchase would benefit the seller."
    }
    
    criteria_description = criteria_descriptions.get(property_criteria, "")
    st.sidebar.markdown(f"**Description:** {criteria_description}")
    
    # Add initial message template
    st.sidebar.header('Initial Message Template')
    default_initial_message = st.session_state.get('initial_message', f"Hey there! I'm {agent_name} from {company}. I work with investors and was wondering if you might have any off-market properties in {region} that could be a good fit?")
    initial_message = st.sidebar.text_area('Initial Message', value=default_initial_message, height=100)
    
    st.session_state['agent_name'] = agent_name
    st.session_state['company'] = company
    st.session_state['region'] = region
    st.session_state['audience_type'] = audience_type
    st.session_state['initial_message'] = initial_message
    st.session_state['property_criteria'] = property_criteria
    st.session_state['criteria_description'] = criteria_description
    
    return agent_name, company, region, audience_type, initial_message, property_criteria, criteria_description

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
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def get_embedding(text, model=EMBEDDING_MODEL):
    response = openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search(query, data, top_k=3, min_similarity=0.85, audience_type=None):
    query_emb = get_embedding(query)
    results = []
    for category, items in data.items():
        # Filter by audience type if possible (category or item field)
        if audience_type:
            if audience_type.lower() == 'realtor' and 'realtor' not in category.lower():
                continue
            if audience_type.lower() == 'homeowner' and 'homeowner' not in category.lower():
                continue
        for item in items:
            if item.get('question', '').strip().upper().startswith('INTERNAL:'):
                continue
            item_emb = item.get('embedding')
            if item_emb:
                sim = cosine_similarity(query_emb, item_emb)
                results.append((sim, category, item))
    results.sort(reverse=True, key=lambda x: x[0])
    
    # Return empty list if no good matches (higher threshold)
    if not results or results[0][0] < min_similarity:
        return []
    
    return results[:top_k]

def generate_llm_response(user_input, top_qas, system_prompt, history):
    # Check for special case questions that must always be answered
    is_asking_what_looking_for = "what are you looking for" in user_input.lower() or "what do you look for" in user_input.lower()
    
    # First, check if this is a simple message that shouldn't use knowledge base
    simple_messages = ["yes", "no", "ok", "sounds good", "call me", "tomorrow", "later", "sure"]
    is_simple_message = any(simple in user_input.lower() for simple in simple_messages) and len(user_input.split()) < 5
    
    # Compose context for the LLM
    context = ""
    
    # Special handling for "what are you looking for"
    if is_asking_what_looking_for and 'property_criteria' in st.session_state and 'criteria_description' in st.session_state:
        context = f"""
IMPORTANT: The user is asking what properties you're looking for. ALWAYS answer this directly using the criteria below:
Property Criteria: {st.session_state['property_criteria']}
Description: {st.session_state['criteria_description']}

Please respond conversationally using this information, explaining what types of properties you're seeking.
"""
    elif top_qas and not is_simple_message:
        context = "Relevant Q&A from our knowledge base:\n"
        for i, (sim, category, item) in enumerate(top_qas):
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
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --- Streamlit UI ---
st.title("QA Chatbot Demo")
st.write("Ask a question and get an answer from your knowledge base!")

agent_name, company, region, audience_type, initial_message, property_criteria, criteria_description = get_custom_fields()
data = load_data()
history = get_history()

# Display initial message template
# st.subheader("Initial Outreach Message")
# st.info(initial_message)
if st.button("Send Initial Message") and not history:
    add_to_history('assistant', initial_message)
    st.rerun()

# # Display property criteria
# st.subheader("Property Criteria")
# st.info(f"Category: {property_criteria}\n\nDescription: {criteria_description}")

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
    system_prompt = BASE_PROMPT + f"\nAgent Name: {agent_name}\nCompany: {company}\nRegion: {region}\nAudience Type: {audience_type}\nProperty Criteria: {property_criteria}\nCriteria Description: {criteria_description}"
    query = system_prompt + user_input
    with st.spinner("Searching for the best answer..."):
        top_results = search(query, data, top_k=3, audience_type=audience_type)
        if top_results:
            llm_response = generate_llm_response(user_input, top_results, system_prompt, history)
            add_to_history('assistant', llm_response)
            st.rerun()
        else:
            add_to_history('assistant', "Sorry, I couldn't find a relevant answer.")
            st.rerun() 

