# AI-Powered Research Paper Intelligence System

An intelligent document ingestion, metadata extraction, NLP preprocessing, and search retrieval platform for academic research papers.

---

## 📌 Architecture Overview

```
PDF / Research Paper
        ↓
PDF Text Extraction (PyMuPDF / pdfplumber)
        ↓
Text Preprocessing & NLP (NLTK / scikit-learn TF-IDF)
        ↓
MySQL Relational Database (Users, Papers, Sections, Keywords)
        ↓
Search & Retrieval Engine (Full-Text & Keyword Matching)
        ↓
Interactive Web Interface (HTML5 / CSS3 / Vanilla JS)
```

---

## 📂 Project Structure

```
research-paper-system/
├── backend/
│   ├── main.py                      # FastAPI application entry point & CORS configuration
│   ├── routes/
│   │   ├── auth.py                  # User authentication & JWT endpoints
│   │   ├── documents.py             # PDF upload, document listing, & management
│   │   └── search.py                # Full-text & keyword search endpoints
│   ├── database/
│   │   ├── connection.py            # MySQL SQLAlchemy connection & session manager
│   │   └── models.py                # ORM Models (User, Paper, PaperSection, PaperKeyword, SearchLog)
│   ├── services/
│   │   ├── pdf_extractor.py         # PDF parsing, page extraction, section splitting
│   │   ├── text_processor.py        # Text cleaning, stopword removal, TF-IDF keyword extraction
│   │   └── search_engine.py         # Ranking, scoring, and query execution logic
│   └── utils/
│       └── helpers.py               # Utility functions & response formatters
├── frontend/
│   ├── index.html                   # Landing page
│   ├── dashboard.html               # Overview dashboard & statistics
│   ├── upload.html                  # PDF upload interface
│   ├── search.html                  # Search & query engine UI
│   ├── papers.html                  # Document repository & library
│   ├── viewer.html                  # Structured paper reader
│   ├── css/style.css                # Global stylesheet
│   └── js/app.js                    # Client-side API integration
├── uploads/                         # Storage directory for uploaded PDF documents
├── tests/
│   ├── test_main.py                 # Backend API endpoint tests
│   └── test_db_connection.py        # Database connectivity & table creation tests
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore rules
└── README.md                        # Documentation
```

---

## 🚀 Quickstart Guide

### 1. Clone / Navigate to the Repository
```bash
cd research-paper-system
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your MySQL credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=research_paper_db
```

### 5. Create MySQL Database & Tables
Create the database in MySQL:
```sql
CREATE DATABASE IF NOT EXISTS research_paper_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run the automated connection & table creation test:
```bash
python tests/test_db_connection.py
```

### 6. Run the Backend API
```bash
uvicorn backend.main:app --reload --port 8000
```

Access the interactive Swagger API documentation:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧪 Running Automated Tests

```bash
python tests/test_main.py
```

---

## 🛠️ Technologies Used

* **Backend Framework:** FastAPI (Python 3.10+)
* **ASGI Web Server:** Uvicorn
* **Database:** MySQL (InnoDB, `utf8mb4`)
* **ORM:** SQLAlchemy 2.0+ & PyMySQL
* **PDF Extraction:** PyMuPDF (`fitz`) / pdfplumber
* **NLP & Text Processing:** NLTK, scikit-learn
* **Frontend:** HTML5, CSS3, Modern JavaScript
