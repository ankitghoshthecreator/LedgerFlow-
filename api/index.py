"""
Vercel Serverless Function entrypoint for FastAPI backend.

This allows Vercel to host BOTH the React Frontend and FastAPI Backend
under one single free project domain without needing any paid services!
"""
import sys
import os

# Add backend directory to sys.path so app imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
