import os
import sys

# Add backend directory to sys.path so app and its dependencies can be imported
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Ensure serverless runtime flag is set
os.environ.setdefault("VERCEL", "1")

from app import app

# Vercel serverless function entrypoint
if __name__ == "__main__":
    app.run()
