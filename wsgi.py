"""
============================================
WSGI Entry Point for Production Deployment
============================================
Used by Gunicorn on Render / Railway / Heroku.

Start command:
    gunicorn wsgi:app --workers 2 --timeout 120 --bind 0.0.0.0:$PORT
"""

import sys
from pathlib import Path

# Ensure project root is on Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
