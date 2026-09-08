import sys
import os

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.database.connection import engine, Base, DB_HOST, DB_PORT, DB_USER, DB_NAME
# Import models so Base.metadata knows about all tables
from backend.database import models


def test_connection():
    """
    Tests connectivity to MySQL and verifies table creation.
    """
    print("=" * 60)
    print(" Research Paper Intelligence System - Database Test")
    print("=" * 60)
    print(f"Target Host: {DB_HOST}:{DB_PORT}")
    print(f"Target User: {DB_USER}")
    print(f"Target Database: {DB_NAME}")
    print("-" * 60)

    try:
        # Step 1: Test raw connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION();"))
            version = result.scalar()
            print(f"[SUCCESS] Connected to MySQL Server! Version: {version}")

        # Step 2: Create all tables defined in models.py
        print("[INFO] Creating database tables if they do not exist...")
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] All tables (users, papers, paper_sections, paper_keywords, search_logs) verified!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"[ERROR] Database connection failed:")
        print(f"Details: {str(e)}")
        print("\nTroubleshooting Tips:")
        print("1. Ensure MySQL server is running (e.g. MySQL Workbench, XAMPP, or Windows Services).")
        print(f"2. Ensure database '{DB_NAME}' has been created: `CREATE DATABASE {DB_NAME};`")
        print("3. Verify DB_USER and DB_PASSWORD in your .env file.")
        print("=" * 60)
        return False


if __name__ == "__main__":
    test_connection()
