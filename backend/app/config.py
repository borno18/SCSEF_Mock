import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Required secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Frontend origin (CORS)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

# Validate required variables and fail loudly at startup if missing
missing_secrets = []
if not OPENAI_API_KEY:
    missing_secrets.append("OPENAI_API_KEY")
if not DATABASE_URL:
    missing_secrets.append("DATABASE_URL")

if missing_secrets:
    print(f"CRITICAL ERROR: Missing required environment variable(s): {', '.join(missing_secrets)}", file=sys.stderr)
    print("Please configure them in your .env file or environment.", file=sys.stderr)
    sys.exit(1)
