"""Vercel Serverless Function entry point for FastAPI application."""

import os
import sys

# Ensure backend root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402

# Vercel's Python runtime discovers the ASGI 'app' object
