import sys
import os
import subprocess

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Check and auto-import or prompt for required dependencies
REQUIRED_PACKAGES = {
    "sqlalchemy": "sqlalchemy",
    "pymysql": "pymysql",
    "dotenv": "python-dotenv",
    "cryptography": "cryptography"
}

missing_packages = []
for module_name, pip_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        missing_packages.append(pip_name)

if missing_packages:
    print(f"[!] Missing required libraries: {', '.join(missing_packages)}")
    print("[*] Installing missing dependencies automatically...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("[OK] Dependencies installed successfully!\n")
    except Exception as e:
        print(f"[ERROR] Auto-install failed. Please run manually:")
        print(f"    pip install {' '.join(missing_packages)}")
        sys.exit(1)

from sqlalchemy import inspect
from backend.database.connection import engine, DB_NAME, DB_HOST, DB_PORT

def inspect_database():
    """
    Connects to MySQL and prints all tables and their columns in detail.
    """
    print("=" * 65)
    print("  MySQL Database Schema Inspector")
    print("=" * 65)
    print(f"Target Host:     {DB_HOST}:{DB_PORT}")
    print(f"Database Name:   {DB_NAME}")
    print("-" * 65)

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            print("[!] No tables found in the database.")
            print("Tip: Run `python tests/test_db_connection.py` to create the tables.")
            print("=" * 65)
            return

        print(f"[OK] Found {len(tables)} table(s) in '{DB_NAME}':\n")

        for table_name in sorted(tables):
            print(f">> Table: {table_name}")
            print("   " + "-" * 55)
            print(f"   {'Column Name':<25} {'Data Type':<20} {'Nullable':<10}")
            print("   " + "-" * 55)

            columns = inspector.get_columns(table_name)
            for col in columns:
                nullable = "YES" if col.get("nullable", True) else "NO"
                print(f"   {col['name']:<25} {str(col['type']):<20} {nullable:<10}")

            pk_constraint = inspector.get_pk_constraint(table_name)
            pks = pk_constraint.get("constrained_columns", [])
            if pks:
                print(f"   Primary Key: {', '.join(pks)}")

            fks = inspector.get_foreign_keys(table_name)
            if fks:
                for fk in fks:
                    ref_table = fk.get("referred_table")
                    cols = ", ".join(fk.get("constrained_columns", []))
                    ref_cols = ", ".join(fk.get("referred_columns", []))
                    print(f"   Foreign Key: ({cols}) -> {ref_table}({ref_cols})")

            print()

        print("=" * 65)

    except Exception as e:
        print(f"[ERROR] Could not connect to database: {e}")
        print("Please ensure your MySQL server is running and .env credentials are correct.")
        print("=" * 65)

if __name__ == "__main__":
    inspect_database()
