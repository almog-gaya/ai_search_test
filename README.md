# Real Estate AI Assistant

A chatbot UI for a real estate assistant that helps gather property details in a conversational manner.

## Deployment Options

### 1. Deploy on Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository, branch (main), and the main file path (chatbot_ui.py)
6. Add your OpenAI API key as a secret:
   - In the app settings, go to "Secrets"
   - Add your API key in this format:
     ```
     [openai]
     api_key = "your-api-key-here"
     ```
7. Deploy!

### 2. Deploy Locally

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key as an environment variable:
   ```
   # On macOS/Linux
   export OPENAI_API_KEY=your-api-key-here
   
   # On Windows
   set OPENAI_API_KEY=your-api-key-here
   ```
4. Run the application:
   ```
   streamlit run chatbot_ui.py
   ```

### 3. Deploy on Other Cloud Platforms

#### Heroku

1. Create a new Heroku app
2. Connect your GitHub repository
3. Add your OpenAI API key as a config var
4. Deploy the app

#### Docker

1. Create a Dockerfile:
   ```
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY . .
   RUN pip install -r requirements.txt
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "chatbot_ui.py"]
   ```
2. Build and run the Docker image:
   ```
   docker build -t real-estate-chatbot .
   docker run -p 8501:8501 -e OPENAI_API_KEY=your-api-key real-estate-chatbot
   ```

## Important Notes

- Make sure to upload or generate the `QA_json2_with_embeddings.json` file on your deployment server
- Never commit your API key to the repository
- Set up proper environment variables on your deployment platform 