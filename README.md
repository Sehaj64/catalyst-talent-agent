# 🤖 Catalyst AI: Advanced Talent Agent

Catalyst AI is an autonomous recruiting agent that performs semantic matching between Job Descriptions and Resumes, followed by automated conversational engagement to qualify candidates.

## 🚀 Features
- **Semantic Matching**: Beyond keyword matching, it understands context using Gemini 1.5.
- **Autonomous Engagement**: Generates dynamic interview questions based on JD requirements.
- **ROI Ranking**: Combines technical fit and conversational interest into a final score.

## 🛠️ Setup Instructions

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up your API Key**:
   - Create a `.streamlit/secrets.toml` file in the root directory.
   - Add your Gemini API key:
     ```toml
     GEMINI_API_KEY = "your_google_api_key_here"
     ```
   - Alternatively, set an environment variable: `export GOOGLE_API_KEY="your_key_here"`

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

## 🔍 Troubleshooting

If the application is "not working", check the following:

### 1. API Key Issues
- **Error**: "API Key Missing!"
- **Fix**: Ensure `GEMINI_API_KEY` is in `.streamlit/secrets.toml` or `GOOGLE_API_KEY` is in your environment.

### 2. Import Errors
- **Error**: `ModuleNotFoundError: No module named 'src'`
- **Fix**: We've added `sys.path.append` to `app.py` to fix this. Ensure you run the app from the root directory of the project.

### 3. File Parsing Failures
- **Error**: "Could not extract text from Job Description"
- **Fix**: Ensure your PDFs/DOCX files are not password-protected or corrupted. The app now includes better error logging for these cases.

### 4. AI Analysis Failures
- **Error**: "AI Job Analysis failed" or "AI Match Calculation failed"
- **Fix**: 
  - Check your internet connection.
  - Verify your Gemini API key has access to the `gemini-1.5-flash` model.
  - The app now uses robust JSON parsing with fallbacks to handle inconsistent LLM responses.

### 5. Dependency Issues
- Ensure all packages in `requirements.txt` are installed. If you see errors related to `docx` or `pypdf`, try reinstalling them:
  ```bash
  pip install --force-reinstall python-docx pypdf
  ```

## 🏗️ Project Structure
- `app.py`: Main Streamlit dashboard and UI logic.
- `src/utils.py`: Core logic for file parsing, Gemini API interaction, and matching algorithms.
- `requirements.txt`: List of required Python packages.
