from __future__ import annotations
import sys
from pathlib import Path

# Ensure root project directory is in python path for Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import server

class handler(server.BaseApiHandler):
    """Vercel Serverless Function entrypoint."""
    pass
