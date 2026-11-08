# ResumeIQ — AI-Powered Resume Analyzer

A full-stack Python web application that compares a candidate's resume with a target job description and provides a match score, skill gaps, detected resume sections, and improvement suggestions.

> **Important:** This is an educational, AI-assisted demo. It uses TF-IDF text similarity and a curated skill keyword list; it does not call a generative AI service and does not predict hiring outcomes.

## Features

- User registration, login, and logout
- Password hashing
- Resume upload: PDF, DOCX, and TXT (5 MB maximum)
- Resume text extraction
- Job-description comparison using TF-IDF and cosine similarity
- Skill matching and missing-skill detection
- Resume section detection and improvement suggestions
- SQLite database and per-user analysis history
- Responsive interface

## Technology stack

- Backend: Python, Flask
- Frontend: HTML, CSS, Jinja templates
- Database: SQLite, Flask-SQLAlchemy
- Text processing: scikit-learn, pdfplumber, python-docx

## Requirements

- Python 3.10 or newer
- pip
- VS Code (recommended)

## Setup on Windows (VS Code)

1. Extract the ZIP file.
2. Open the extracted `ai_resume_analyzer` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   py -m venv venv
   ```

5. Activate it:

   ```powershell
   .\\venv\\Scripts\\Activate.ps1
   ```

   If PowerShell blocks activation, run this once in the current terminal:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\\venv\\Scripts\\Activate.ps1
   ```

6. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Start the application:

   ```powershell
   python app.py
   ```

8. Open this address in your browser:

   `http://127.0.0.1:5000`

9. Create an account, sign in, choose **New analysis**, upload a resume, and paste a job description.

## Setup on macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Then visit `http://127.0.0.1:5000`.

## Project structure

```text
ai_resume_analyzer/
├── app.py
├── analyzer.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── analyze.html
│   └── result.html
├── static/
│   └── style.css
└── uploads/
```

The SQLite database (`resume_analyzer.db`) is created automatically on first run. Uploaded files are stored in `uploads/`.

## How the score works

When job-description skills are detected:

`Match score = 65% × skill coverage + 35% × TF-IDF similarity`

Skill coverage is the fraction of detected job skills also found in the resume. If no known skills are found in the job description, the score uses text similarity alone. This is a simple transparent heuristic, not an industry-standard ATS score.

## Troubleshooting

- **`py` is not recognized:** Install Python from python.org and select “Add Python to PATH”, then reopen VS Code.
- **`ModuleNotFoundError`:** Activate `venv` and run `pip install -r requirements.txt`.
- **PDF has no extracted text:** It may be a scanned image. This starter project does not include OCR; try a text-based PDF or DOCX.
- **Port 5000 is busy:** Change the final line in `app.py` to `app.run(debug=True, port=5001)` and visit port 5001.
- **PowerShell activation blocked:** Use the process-scoped execution policy command shown above.

## Before production deployment

This is a learning project, not a production-ready service. Before public deployment:
- Set a strong random `SECRET_KEY` through an environment variable.
- Turn off Flask debug mode.
- Add CSRF protection, rate limiting, and stricter upload validation.
- Store uploads outside the public web root and add retention/deletion controls.
- Use HTTPS and a production database.
- Add malware scanning and privacy/consent notices.
