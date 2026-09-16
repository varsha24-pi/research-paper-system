# AI-Powered Research Paper Intelligence System
> **A Comprehensive Academic Document Ingestion, NLP Preprocessing, Metadata Extraction, and Information Retrieval Platform**  
> *Undergraduate Minor Project in Computer Science & Engineering*

---

## 📋 Table of Contents
1. [Project Title & Header](#-project-title)
2. [Introduction](#-introduction)
3. [Problem Statement](#-problem-statement)
4. [Objectives](#-objectives)
5. [Key Features](#-key-features)
6. [System Architecture](#-system-architecture)
7. [Technologies Used](#-technologies-used)
8. [Project Directory Structure](#-project-directory-structure)
9. [Installation & Setup](#-installation--setup)
10. [Database Configuration](#-database-configuration)
11. [Running the Backend API](#-running-the-backend-api)
12. [Running the Frontend Interface](#-running-the-frontend-interface)
13. [REST API Documentation & Endpoints](#-rest-api-documentation--endpoints)
14. [Search & Information Retrieval Methodology](#-search--information-retrieval-methodology)
15. [AI / NLP Preprocessing Methodology](#-ai--nlp-preprocessing-methodology)
16. [Automated Testing & Quality Assurance](#-automated-testing--quality-assurance)
17. [Current System Limitations](#-current-system-limitations)
18. [Future Scope & Enhancements](#-future-scope--enhancements)
19. [Conclusion](#-conclusion)

---

## 🎓 1. Project Title
**AI-Powered Research Paper Intelligence System**  
An end-to-end intelligent research platform designed to automate the ingestion, structural analysis, metadata extraction, and relevance-ranked retrieval of academic research PDF papers.

---

## 📖 2. Introduction
Academic literature is expanding exponentially across various disciplines. Researchers, university students, and faculty members face significant challenges in discovering, organizing, and synthesizing insights from hundreds of multi-page PDF documents. Traditional desktop file explorers and basic keyword matching tools lack domain-specific semantic understanding, cannot differentiate between section boundaries (such as *Abstract*, *Methodology*, and *Results*), and offer no mathematical ranking of relevance.

The **AI-Powered Research Paper Intelligence System** bridges this gap by integrating modern high-speed PDF parsing (**PyMuPDF**), statistical natural language processing (**TF-IDF & Vector Space Models**), transactional relational storage (**MySQL & SQLAlchemy**), and an asynchronous web backend (**FastAPI**). The result is a centralized research repository capable of extracting structural intelligence and retrieving contextual snippets with sub-second query latency.

---

## ❗ 3. Problem Statement
1. **Unstructured Data Silos**: Research papers are primarily distributed in PDF format—a presentation format optimized for printing rather than programmatic text analysis.
2. **Inefficient Search Paradigms**: Standard database queries (`SQL LIKE %keyword%`) perform naive binary substring matches without term weighting, frequency analysis, or relevance scoring.
3. **Manual Overhead in Cataloging**: Manually reading through papers to determine the title, authors, publication year, key concepts, and section boundaries is labor-intensive.
4. **Lack of Explainability in Retrieval**: Existing search engines often act as black boxes, providing no visibility into why a document was ranked higher or which specific passage matched the user's inquiry.

---

## 🎯 4. Objectives
* **Automated Document Ingestion**: Implement secure validation, upload, and text parsing for arbitrary academic research papers in PDF format.
* **Structural & Metadata Intelligence**: Automatically isolate paper titles, author lists, publication years, explicit keywords, and core academic sections (*Abstract*, *Introduction*, *Methodology*, *Results*, *Conclusion*).
* **Statistical NLP Concept Extraction**: Extract domain-specific keywords and assign quantitative relevance weights using unigram and bigram TF-IDF analysis.
* **Vector Space Information Retrieval**: Implement a TF-IDF and Cosine Similarity search engine that scores and ranks documents transparently between $0.0$ and $1.0$ ($0\% - 100\%$).
* **Context Snippet Generation**: Extract contextual text windows around matched keywords to facilitate rapid visual evaluation on the frontend.
* **Security & Multi-Tenant Access**: Enforce `bcrypt` password hashing and stateless JSON Web Token (`JWT`) authentication for user accounts.

---

## ✨ 5. Key Features
* 📄 **High-Performance PDF Text Parsing**: Powered by PyMuPDF (`fitz`), enabling page-by-page extraction with line-hyphenation repairs and control-character filtering.
* 🏷️ **Rule-Based & Heuristic Metadata Extraction**: Distinguishes paper titles from publisher/conference headers, strips academic affiliations from author names, and extracts publication years.
* 📑 **Section-Level Document Segmentation**: Regex-driven boundary detection splits research text into logical academic sections.
* 🔍 **TF-IDF & Cosine Similarity Search**: Vector Space Model information retrieval with logarithmic term frequency scaling (`sublinear_tf=True`) and Euclidean L2 normalization.
* 💬 **Dynamic Highlighted Snippets**: Generates 200-character context snippets with highlighted query tokens for instant preview.
* 📊 **Query Logging & Audit Analytics**: Records all search queries, timestamps, and result counts in MySQL for system analytics.
* 🛡️ **Upload Security & MIME Verification**: Validates PDF file extensions, MIME headers, and `%PDF` magic bytes to prevent malicious file execution.
* 🔐 **Secure User Authentication**: Bcrypt-hashed credentials with RFC 7519-compliant JWT access tokens.
* 💻 **Academic Frontend UI**: Clean, responsive interface built in vanilla HTML5, CSS3, and JavaScript without bloated frameworks.

---

## 🏛️ 6. System Architecture

```
                                  +---------------------------------------+
                                  |         User Browser / Client         |
                                  | (HTML5 / Modern CSS3 / Vanilla JS)    |
                                  +-------------------+-------------------+
                                                      |
                                     HTTP REST / JSON | Multipart Form
                                                      v
+---------------------------------------------------------------------------------------------------------+
|                                        FastAPI Backend Application                                      |
|                                                                                                         |
|  +---------------------------+   +----------------------------+   +----------------------------------+  |
|  |   Authentication Router   |   |      Documents Router      |   |          Search Router           |  |
|  |     (/auth/login, etc.)   |   |     (/documents/upload)    |   |         (/search/?q=...)         |  |
|  +-------------+-------------+   +--------------+-------------+   +------------------+---------------+  |
|                |                                |                                    |                  |
+----------------|--------------------------------|------------------------------------|------------------+
                 |                                |                                    |
                 v                                v                                    v
   +---------------------------+    +-----------------------------+     +-------------------------------+
   |   Security / JWT Module   |    |    PyMuPDF Extraction Engine|     |  TF-IDF & Cosine Similarity   |
   | (bcrypt & HMAC-SHA256)    |    |  (Text, Pages, Formatting)  |     |      Vector Search Engine     |
   +---------------------------+    +--------------+--------------+     +---------------+---------------+
                                                   |                                    |
                                                   v                                    |
                                    +-----------------------------+                     |
                                    | NLP Preprocessing & Metadata|                     |
                                    | (Regex, Sections, Keywords) |                     |
                                    +--------------+--------------+                     |
                                                   |                                    |
                                                   v                                    v
+---------------------------------------------------------------------------------------------------------+
|                                       MySQL Relational Database                                         |
|                                                                                                         |
|   +-------------------+   +--------------------+   +-----------------------+   +--------------------+   |
|   |    users Table    |   |    papers Table    |   | paper_sections Table  |   | paper_keywords Tbl |   |
|   +-------------------+   +--------------------+   +-----------------------+   +--------------------+   |
+---------------------------------------------------------------------------------------------------------+
```

### End-to-End Ingestion Pipeline
1. **Upload**: User uploads PDF via `POST /documents/upload` (with optional metadata).
2. **Validation**: Verification of file size ($\le 50\text{ MB}$), MIME type (`application/pdf`), and magic bytes (`%PDF`).
3. **Extraction**: PyMuPDF reads binary streams, extracts page text, and computes word counts.
4. **Preprocessing**: Normalizes whitespace, repairs split hyphenated words, and filters control characters.
5. **Metadata & NLP**: Regex patterns identify Title, Authors, Abstract, Sections, and top TF-IDF keywords.
6. **Relational Storage**: Stores structured entities into `papers`, `paper_sections`, and `paper_keywords` inside an atomic transaction.
7. **Search Indexing**: Queries convert to TF-IDF vectors, compute Cosine Similarity across paper vectors, and rank matching results.

---

## 💻 7. Technologies Used

| Category | Technology | Version | Purpose |
|---|---|---|---|
| **Backend Framework** | **FastAPI** | `^0.100.0` | Asynchronous high-performance REST API |
| **ASGI Server** | **Uvicorn** | `^0.22.0` | Production ASGI web server with hot reloading |
| **Database Engine** | **MySQL** | `8.0+` | Relational data persistence with `utf8mb4` support |
| **ORM Layer** | **SQLAlchemy** | `^2.0.0` | Object Relational Mapping and schema definition |
| **Database Driver** | **PyMySQL** | `^1.1.0` | Python-to-MySQL database driver |
| **PDF Extraction Engine** | **PyMuPDF (`fitz`)** | `^1.23.0` | C-level fast PDF text and metadata parsing |
| **Machine Learning / NLP** | **scikit-learn** | `^1.3.0` | TF-IDF Vectorizer and Cosine Similarity computations |
| **Password Hashing** | **bcrypt** | `^4.0.0` | Adaptive salted password hashing (12 rounds) |
| **Authentication Tokens** | **PyJWT** | `^2.8.0` | RFC 7519 JSON Web Token generation & validation |
| **Testing Framework** | **pytest** | `^8.0.0` | Automated test suite and regression runner |
| **Frontend Technologies**| **HTML5 / CSS3 / Vanilla JS**| — | Responsive academic user interface |

---

## 📂 8. Project Directory Structure

```
research-paper-system/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point, CORS & route registry
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py            # MySQL engine, connection pooling, SessionLocal
│   │   └── models.py                # SQLAlchemy ORM models (User, Paper, PaperSection, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                  # User registration, login, JWT token verification
│   │   ├── documents.py             # Multipart PDF upload, listing, and ID inspection
│   │   └── search.py                # TF-IDF search endpoint & query history
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py         # PyMuPDF text & page parsing engine
│   │   ├── text_processor.py        # Text cleaning, section segmentation, TF-IDF keywords
│   │   ├── metadata_extractor.py    # Heuristic Title, Author, Year, and Abstract extraction
│   │   └── search_engine.py         # Vector Space Model & Cosine Similarity search
│   └── utils/
│       ├── __init__.py
│       └── helpers.py               # Security validation (magic bytes, filenames, hashing)
├── frontend/
│   ├── index.html                   # Academic landing page & live system stats
│   ├── upload.html                  # Drag-and-drop PDF upload interface with pipeline tracker
│   ├── search.html                  # Interactive search page with chips & highlighted snippets
│   ├── dashboard.html               # Analytics & overview dashboard
│   ├── papers.html                  # Paper repository & library browser
│   ├── viewer.html                  # Structured section paper reader
│   ├── css/
│   │   └── style.css                # Global academic theme styling
│   └── js/
│       └── app.js                   # Client-side API integration & formatters
├── tests/
│   ├── conftest.py                  # Pytest fixtures (DB Session, TestClient, in-memory PDF)
│   ├── test_system_suite.py         # 12-scenario system verification test suite
│   ├── test_e2e_workflow.py         # Complete end-to-end integration workflow test
│   ├── run_tests.py                 # Master test execution script with summary table
│   ├── test_auth.py                 # Dedicated authentication test suite
│   ├── test_db_connection.py        # Standalone database connectivity check
│   ├── test_documents_upload.py     # PDF upload & ingestion tests
│   ├── test_metadata_extractor.py   # Heuristic metadata extraction unit tests
│   ├── test_pdf_extractor.py        # PyMuPDF engine unit tests
│   └── test_search_engine.py        # TF-IDF & Cosine similarity tests
├── uploads/                         # Local storage directory for uploaded PDF files
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore configuration
├── requirements.txt                 # Project Python dependencies
├── schema.sql                       # MySQL schema creation script
└── README.md                        # Project documentation
```

---

## ⚙️ 9. Installation & Setup

### Prerequisites
* **Python 3.10 to 3.13** installed on your system.
* **MySQL Server 8.0+** running locally (via MySQL Workbench, XAMPP, or Windows Service).
* **Git** version control.

### Step 1: Clone the Repository
```bash
git clone https://github.com/varsha24-pi/research-paper-system.git
cd research-paper-system
```

### Step 2: Create a Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 🗄️ 10. Database Configuration

### Step 1: Create the MySQL Database
Open **MySQL Workbench** or your terminal client and execute:
```sql
CREATE DATABASE IF NOT EXISTS research_paper_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### Step 2: Configure the Environment File
Copy `.env.example` to create `.env`:
```powershell
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` to match your local MySQL credentials:
```ini
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=research_paper_db

# Security & JWT Settings
SECRET_KEY=your_secure_random_jwt_secret_key_2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=uploads
```

### Step 3: Verify Database Connectivity & Auto-Generate Tables
Run the database test script to automatically create all relational tables:
```bash
python tests/test_db_connection.py
```

---

## 🚀 11. Running the Backend API

Start the FastAPI application using **Uvicorn**:
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
* **API Server Base URL**: `http://127.0.0.1:8000`
* **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
* **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 🌐 12. Running the Frontend Interface

Because the frontend is built entirely in **Vanilla HTML5, CSS3, and JavaScript**, no build steps (like `npm run build` or Webpack) are required.

### Option A: VS Code Live Server (Recommended)
1. Open the project folder in VS Code.
2. Right-click [`frontend/index.html`](file:///d:/Project/implementation/research-paper-system/frontend/index.html) and select **"Open with Live Server"**.
3. Access the interface at `http://127.0.0.1:5500/frontend/index.html`.

### Option B: Direct Browser Open
Double-click [`frontend/index.html`](file:///d:/Project/implementation/research-paper-system/frontend/index.html) to open directly in Chrome, Edge, or Firefox.

---

## 📡 13. REST API Documentation & Endpoints

| Category | HTTP Method | Endpoint | Description | Auth Required |
|---|---|---|---|:---:|
| **System** | `GET` | `/` | Root endpoint displaying system health & metadata | No |
| **System** | `GET` | `/health` | Server uptime and status indicator | No |
| **Auth** | `POST` | `/auth/register` | Register a new researcher account | No |
| **Auth** | `POST` | `/auth/login` | Authenticate user & receive JWT access token | No |
| **Auth** | `GET` | `/auth/me` | Fetch authenticated user profile details | **Yes** (Bearer) |
| **Documents** | `POST` | `/documents/upload` | Upload PDF, extract sections, and save to MySQL | Optional |
| **Documents** | `GET` | `/documents/` | List all indexed papers (with pagination) | No |
| **Documents** | `GET` | `/documents/{id}` | Retrieve full structured paper, sections, & keywords | No |
| **Documents** | `GET` | `/documents/user/my-papers` | Fetch papers uploaded by current user | **Yes** (Bearer) |
| **Search** | `GET` | `/search/` | TF-IDF & Cosine Similarity search with query snippets | No |
| **Search** | `GET` | `/search/history` | Retrieve recent search queries and analytics | No |

---

## 🔍 14. Search & Information Retrieval Methodology

The system uses the **Vector Space Model (VSM)** with **TF-IDF (Term Frequency-Inverse Document Frequency)** and **Cosine Similarity** to score and rank documents:

### 1. Document Composite Representation
For each paper $d$, a weighted text document is constructed:
$$\text{Corpus}(d) = (\text{Title} \times 3) + (\text{Abstract} \times 2) + \text{Keywords} + \text{Sections}$$

### 2. Term Frequency ($TF$) with Sublinear Scaling
To prevent long documents with repeated words from distorting results, sublinear scaling is applied:
$$\text{TF}(t, d) = 1 + \log(\text{count}(t, d)) \quad \text{for } \text{count}(t, d) > 0$$

### 3. Inverse Document Frequency ($IDF$)
Measures the rarity of a term across the entire corpus of $N$ papers:
$$\text{IDF}(t) = \log\left(\frac{1 + N}{1 + \text{DF}(t)}\right) + 1$$

### 4. Vector Weight Computation & Euclidean Normalization
$$\mathbf{V}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)$$
Vectors are normalized to unit length ($\|\mathbf{V}\|_2 = 1$).

### 5. Cosine Similarity Ranking
Given a query vector $\mathbf{q}$ and document vector $\mathbf{d}$:
$$\text{Cosine Similarity}(\mathbf{q}, \mathbf{d}) = \cos(\theta) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \|\mathbf{d}\|_2} = \sum_{i=1}^{M} q_i \cdot d_i$$

The resulting score ($0.0 \le \text{Score} \le 1.0$) is converted to a human-readable percentage ($0\% - 100\%$) and ranked in descending order.

---

## 🧠 15. AI / NLP Preprocessing Methodology

```
Raw PDF Binary ──► PyMuPDF Page Text ──► Text Normalization ──► Regex Boundary Split ──► TF-IDF Keyphrase Extraction
```

1. **Text Normalization**: Strips unprintable control characters (`\x00-\x1f`), normalizes 3+ newlines, and corrects line-broken hyphenated words (`trans-\nformer` $\rightarrow$ `transformer`).
2. **Abstract Detection**: Captures text between the keyword `Abstract` and standard start headings (e.g. `1 Introduction`).
3. **Academic Section Splitting**: Scans for standard structural markers (`Abstract`, `Introduction`, `Related Work`, `Methodology`, `Results`, `Discussion`, `Conclusion`, `References`).
4. **Stopword Elimination**: Combines standard English stopwords with academic noise words (`et`, `al`, `proceedings`, `journal`, `volume`, `figure`, `table`, `doi`).
5. **N-Gram Keyphrase Extraction**: Evaluates both unigrams (e.g., `transformer`) and bigrams (e.g., `attention mechanism`, `neural network`).

---

## 🧪 16. Automated Testing & Quality Assurance

The system includes a 12-point automated verification suite built using `pytest` and FastAPI's `TestClient`:

### Run the Master Test Runner
```bash
python tests/run_tests.py
```

### Run Tests via Pytest CLI
```bash
pytest -v tests/test_system_suite.py
pytest -v tests/test_e2e_workflow.py
```

### Verified Test Cases:
1. ✅ **Database Connection**: Tests live ping and verifies table schema creation.
2. ✅ **User Registration**: Verifies user creation (HTTP 201) and duplicate user rejection (HTTP 400).
3. ✅ **User Login**: Tests invalid password rejection (HTTP 401) and valid JWT generation (HTTP 200).
4. ✅ **PDF Upload**: Verifies multipart upload and extraction pipeline execution.
5. ✅ **Invalid File Rejection**: Ensures `.txt` and spoofed non-PDF files are rejected.
6. ✅ **PyMuPDF Extraction**: Tests multi-page extraction, word counts, and empty page handling.
7. ✅ **Text Preprocessing**: Validates text cleaning, abstract extraction, and sectioning.
8. ✅ **Relational Storage**: Queries MySQL directly to verify foreign key integrity across child tables.
9. ✅ **Search with Valid Query**: Verifies positive cosine similarity score and 200-char context snippets.
10. ✅ **Search with Zero Matches**: Validates graceful empty state handling without server exceptions.
11. ✅ **Metadata Extraction**: Evaluates heuristic title, author, year, and keyword parsing.
12. ✅ **API Error Handling**: Verifies HTTP status codes for 400, 401, 404, 413, and 422 edge cases.

---

## ⚠️ 17. Current System Limitations
1. **Scanned / Image-Only PDFs**: The current engine extracts digital text embedded in PDFs. Scanned image papers (without an optical text layer) require an external OCR engine (like Tesseract).
2. **Vocabulary Sparsity on Tiny Corpora**: If the database contains only 1 or 2 papers, TF-IDF cannot establish strong statistical variance across terms.
3. **Exact Word Matching in TF-IDF**: Pure TF-IDF matches statistical lexical terms; synonymous terms not appearing in the text (e.g. searching "automobile" when the paper says "car") require semantic embedding models.

---

## 🔮 18. Future Scope & Enhancements
* **Dense Semantic Embeddings**: Integrating lightweight embedding models (e.g., `sentence-transformers/all-MiniLM-L6-v2`) with vector indexing (FAISS or ChromaDB) for semantic retrieval.
* **LLM-Powered Summarization (RAG)**: Adding Retrieval-Augmented Generation with an open-source LLM (e.g. Llama 3 / Mistral) to allow researchers to ask natural language questions directly to papers.
* **OCR Ingestion**: Adding Tesseract OCR support to process scanned historical papers.
* **Citation Network Graph**: Extracting `References` sections to construct interactive citation graph visualizations.

---

## 📌 19. Conclusion
The **AI-Powered Research Paper Intelligence System** successfully addresses the challenge of academic paper discovery by transforming unstructured PDF documents into structured, queryable knowledge. By integrating high-speed extraction (**PyMuPDF**), heuristic metadata extraction, statistical natural language processing (**TF-IDF**), and a modern asynchronous backend (**FastAPI + MySQL**), the project delivers sub-second retrieval times, transparent relevance scoring, and an intuitive user experience suitable for academic research workflows.

---

### 👥 Academic Project Information
* **Course:** Bachelor of Technology / Computer Science & Engineering
* **Project Type:** Minor Project
* **Repository:** [https://github.com/varsha24-pi/research-paper-system](https://github.com/varsha24-pi/research-paper-system)
* **License:** MIT License
