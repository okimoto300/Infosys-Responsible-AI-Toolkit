"""
Responsible AI Toolkit - Questionnaire Service Local Setup

Usage:
    python local-setup.py

This script:
  1. Installs Python dependencies
  2. Configures .env for local execution (mongomock in-memory DB)
  3. Patches DatabaseConnection.py to support mongomock
  4. Starts the service on http://localhost:30080

Open http://localhost:30080/v1/questionnaire/docs in your browser.
"""
import subprocess
import sys
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
ENV_FILE = SRC_DIR / "questionnaire" / ".env"
DB_FILE = SRC_DIR / "questionnaire" / "dao" / "DatabaseConnection.py"

def main():
    print("=== Responsible AI Toolkit - Questionnaire Service Local Setup ===\n")

    # 1. Install dependencies
    print("[1/4] Installing dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--quiet",
        "fastapi==0.100.1", "pydantic==1.10.11", "requests==2.32.0",
        "requests-file==1.5.1", "uvicorn==0.22.0", "PyYAML", "pymongo",
        "python-dotenv", "python-multipart", "pandas", "chardet==4.0.0",
        "mongomock",
    ])

    # 2. Configure .env
    print("[2/4] Configuring .env...")
    ENV_FILE.write_text("""\
DB_NAME="rai_questionnaire"
PRIVACY_API="http://localhost:30002/v1/privacy/text/analyze"
PROFANITY_API="http://localhost:30003/api/v1/safety/profanity/analyze"
FM_MODERATION_API="http://localhost:8000/rai/v1/moderations"
EXPLAINABILITY_API="http://localhost:30004/v1/explainability/analyze"
SERVERTYPE="LOT"
DB_USERNAME=""
DB_PWD=""
DB_IP="localhost"
DB_PORT="27017"
MONGO_PATH="mongodb://localhost:27017/"
DB_TYPE="mongomock"
COSMOS_PATH=""
allow_origin="*"
allow_method="GET,POST,OPTIONS,HEAD"
VERIFY_SSL="False"
TELEMETRY_ALLOWED_HOSTS="localhost,vimptblt1117"
""")

    # 3. Patch DatabaseConnection.py
    print("[3/4] Patching DatabaseConnection.py for mongomock...")
    content = DB_FILE.read_text()
    if "mongomock" not in content:
        old = """\
            db_type = os.getenv('DB_TYPE', 'mongo').lower()

            # Connect to the appropriate database based on the database type
            if db_type == 'cosmos':"""
        new = """\
            db_type = os.getenv('DB_TYPE', 'mongo').lower()

            if db_type == 'mongomock':
                import mongomock
                myclient = mongomock.MongoClient()
            elif db_type == 'cosmos':"""
        if old in content:
            DB_FILE.write_text(content.replace(old, new))
            print("  Patched.")
        else:
            print("  WARNING: Could not find expected code block. Manual patch may be needed.")
    else:
        print("  Already patched.")

    # 4. Start service
    print("[4/4] Starting service on port 30080...\n")
    print("==========================================")
    print("  Open in browser:")
    print("  http://localhost:30080/v1/questionnaire/docs")
    print("==========================================\n")

    os.chdir(SRC_DIR)
    subprocess.check_call([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0", "--port", "30080",
    ])

if __name__ == "__main__":
    main()
