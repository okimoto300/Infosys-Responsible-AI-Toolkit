#!/bin/bash
set -e

echo "=== Responsible AI Toolkit - Questionnaire Service Local Setup ==="
echo ""

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
SRC_DIR="$PROJECT_DIR/src"
ENV_FILE="$SRC_DIR/questionnaire/.env"
DB_FILE="$SRC_DIR/questionnaire/dao/DatabaseConnection.py"

# 1. Install dependencies
echo "[1/4] Installing dependencies..."
pip install fastapi==0.100.1 pydantic==1.10.11 requests==2.32.0 requests-file==1.5.1 \
  uvicorn==0.22.0 PyYAML pymongo python-dotenv python-multipart pandas chardet==4.0.0 mongomock \
  --quiet

# 2. Configure .env
echo "[2/4] Configuring .env..."
cat > "$ENV_FILE" <<'ENVEOF'
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
ENVEOF

# 3. Patch DatabaseConnection.py for mongomock support
echo "[3/4] Patching DatabaseConnection.py for mongomock..."
if ! grep -q "mongomock" "$DB_FILE"; then
  sed -i.bak "s|db_type = os.getenv('DB_TYPE', 'mongo').lower()|db_type = os.getenv('DB_TYPE', 'mongo').lower()\n\n            if db_type == 'mongomock':\n                import mongomock\n                myclient = mongomock.MongoClient()\n            el|" "$DB_FILE"
  # Fix the double 'el' issue - replace 'elif' that follows
  sed -i "s|            el            # Connect to the appropriate database based on the database type\n            if|            elif|" "$DB_FILE" 2>/dev/null || true
  echo "  Patched."
else
  echo "  Already patched."
fi

# 4. Start the service
echo "[4/4] Starting service on port 30080..."
echo ""
echo "=========================================="
echo "  Open in browser:"
echo "  http://localhost:30080/v1/questionnaire/docs"
echo "=========================================="
echo ""
cd "$SRC_DIR"
python -m uvicorn main:app --host 0.0.0.0 --port 30080
