import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------------------------------------------------------
# 1. Application Initialization & Metadata
# -----------------------------------------------------------------------------
app = FastAPI(
    title="AI-Powered Research Paper Intelligence System",
    description=(
        "Backend API for extracting text, processing research papers, "
        "indexing content in MySQL, and providing intelligent search capabilities."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# -----------------------------------------------------------------------------
# 2. CORS (Cross-Origin Resource Sharing) Configuration
# -----------------------------------------------------------------------------
# Enables the frontend (running on a different port/domain or opened via browser)
# to securely communicate with this FastAPI backend.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
    "*"  # Permissive during local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],  # Allows all headers such as Authorization and Content-Type
)

# -----------------------------------------------------------------------------
# 3. Router Registration
# -----------------------------------------------------------------------------
from backend.routes import documents
app.include_router(documents.router)

# Future modules to include as they are implemented:
# from backend.routes import auth, search
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# app.include_router(search.router, prefix="/search", tags=["Search & Retrieval"])


# -----------------------------------------------------------------------------
# 4. Core System Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["System"])
def root():
    """
    Root endpoint: Provides system info and direct link to API docs.
    """
    return {
        "status": "online",
        "project": "AI-Powered Research Paper Intelligence System",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint: Used to verify server uptime and connectivity.
    """
    return {
        "status": "healthy",
        "service": "backend-api",
        "uptime": "operational"
    }


# -----------------------------------------------------------------------------
# 5. Direct Execution Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Allows running directly via `python backend/main.py`
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
