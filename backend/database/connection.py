import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Retrieve database credentials from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "research_paper_db")

# Safely escape special characters in password (like @, #, $, etc.)
ENCODED_PASSWORD = quote_plus(DB_PASSWORD)

# Construct MySQL SQLAlchemy Connection URL using PyMySQL driver
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{ENCODED_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# Create the SQLAlchemy engine
# - pool_pre_ping=True: Automatically checks if connection is alive before executing queries
# - pool_recycle=3600: Prevents MySQL from dropping stale idle connections (after 1 hour)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True if you want to see raw SQL logs during debugging
)

# Session factory for handling database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency to yield a database session per request
    and ensure proper cleanup/closing after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
