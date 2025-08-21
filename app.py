import os
import json
from flask import Flask, request, jsonify, render_template, g
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import requests
import time 
import re 
import sqlite3 
from datetime import datetime 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set it.")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="

# SQLite Database Configuration
DATABASE = 'resume_data.db'

def get_db():
    """
    Establishes a database connection or returns the existing one.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database connection at the end of the request.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """
    Initializes the database schema if it doesn't exist.
    """
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                job_type TEXT NOT NULL,
                ats_score INTEGER,
                suggestions TEXT
            )
        ''')
        db.commit()

# Call init_db when the application starts
with app.app_context():
    init_db()

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        app.logger.error(f"Error extracting text from PDF: {e}")
        return None

def call_gemini_api_with_retry(prompt, max_retries=5, initial_delay=1):
    """
    Calls the Gemini API with exponential backoff for retries.
    """
    for i in range(max_retries):
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            response = requests.post(f"{GEMINI_API_URL}{GEMINI_API_KEY}", headers=headers, json=payload, timeout=60)
            response.raise_for_status() 
            result = response.json()

            if result and result.get("candidates") and result["candidates"][0].get("content") and \
               result["candidates"][0]["content"].get("parts") and result["candidates"][0]["content"]["parts"][0].get("text"):
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                app.logger.warning(f"Gemini API response format unexpected: {result}")
                return None
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Gemini API call failed (attempt {i+1}/{max_retries}): {e}")
            if i < max_retries - 1:
                time.sleep(initial_delay * (2 ** i)) 
            else:
                app.logger.error("Max retries reached for Gemini API call.")
                return None
    return None

def parse_ats_response(gemini_output):
    """
    Parses the Gemini output for ATS score and suggestions.
    Assumes Gemini output is structured like:
    "ATS Score: 75/100\nSuggestions:\n- Suggestion 1\n- Suggestion 2"
    """
    if not gemini_output:
        return {"atsScore": "N/A", "suggestions": ["Could not get a response from AI."]}

    score = "N/A"
    suggestions = []

    lines = gemini_output.split('\n')
    for line in lines:

        score_match = re.search(r"ATS Score:\s*(\d+)", line)
        if score_match:
            try:
                score = int(score_match.group(1))
            except ValueError:
                pass 
        elif line.strip().startswith("-"):
            suggestions.append(line.strip().lstrip('- ').strip())
        elif "Suggestions:" in line:
            continue 
        elif line.strip(): 
             if not suggestions and "ATS Score:" not in line: 
                 suggestions.append(line.strip())


    if not suggestions and "N/A" not in str(score):
        suggestions = ["No specific suggestions were provided, but ensure your resume closely matches the job description keywords."]
    elif not suggestions: 
        suggestions = ["Could not parse response or no specific suggestions provided. Ensure the job type is clear."]

    return {"atsScore": score, "suggestions": suggestions}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file part"}), 400
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        resume_text = extract_text_from_pdf(filepath)
        os.remove(filepath) 

        if not resume_text:
            return jsonify({"error": "Failed to extract text from PDF. Please ensure it's a searchable PDF."}), 500

        job_type = request.form.get('job_type', 'General Job').strip()
        if not job_type:
            job_type = 'General Job' # Default if not provided

        # Prompt for ATS score and suggestions
        ats_prompt = f"""
        Analyze the following resume text against the job type "{job_type}" to determine an ATS (Applicant Tracking System) compatibility score out of 100.
        Provide actionable suggestions to improve the resume's ATS score for this specific job type.
        Focus on keywords, formatting that might hinder ATS, and overall relevance.
        Structure your response clearly with the ATS Score on one line, followed by a "Suggestions:" heading, and then a bulleted list of suggestions.
        Always include "/100" after the score.

        Resume Text:
        {resume_text}

        Expected Output Format:
        ATS Score: [SCORE]/100
        Suggestions:
        - Suggestion 1
        - Suggestion 2
        """

        gemini_response = call_gemini_api_with_retry(ats_prompt)
        parsed_response = parse_ats_response(gemini_response)

        # Save results to SQLite database
        db = get_db()
        cursor = db.cursor()
        try:
            timestamp = datetime.now().isoformat()
            
            ats_score_val = parsed_response["atsScore"] if isinstance(parsed_response["atsScore"], int) else None
            
            suggestions_json = json.dumps(parsed_response["suggestions"])

            cursor.execute(
                "INSERT INTO results (timestamp, resume_text, job_type, ats_score, suggestions) VALUES (?, ?, ?, ?, ?)",
                (timestamp, resume_text, job_type, ats_score_val, suggestions_json)
            )
            db.commit()
            app.logger.info("Resume analysis results saved to database.")
        except sqlite3.Error as e:
            app.logger.error(f"Error saving data to database: {e}")


        return jsonify({
            "atsScore": parsed_response["atsScore"],
            "suggestions": parsed_response["suggestions"],
            "extracted_text": resume_text # Send extracted text back to frontend
        })
    return jsonify({"error": "Invalid file type. Only PDF is supported."}), 400


if __name__ == '__main__':
    app.run(debug=True) 