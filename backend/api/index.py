"""Vercel Serverless Function entry point for FastAPI application."""

from app.main import app

# Vercel's Python runtime discovers the ASGI 'app' object
