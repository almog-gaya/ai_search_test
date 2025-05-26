# Real Estate QA Chatbot

This is a Streamlit-based chatbot that answers real estate questions using a custom knowledge base and OpenAI's GPT models.

## Features
- Natural language Q&A for real estate
- Uses OpenAI GPT and embeddings
- Fast, simple UI with Streamlit

## How to Run Locally
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `streamlit run chatbot_ui.py`

## Deploy on Streamlit Cloud
1. Push your code to GitHub (already done!)
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click "New app" and select your repo
4. Set the main file to `chatbot_ui.py`
5. Add your OpenAI API key as a secret (see below)

## Secrets (API Keys)
On Streamlit Cloud, set your OpenAI API key in the secrets manager:
```
[openai]
api_key = "sk-..."
```

---

**Note:** The file `QA_JSON_with_embeddings.json` is not included in the repo. You must upload it manually to Streamlit Cloud or provide a way to generate it. 