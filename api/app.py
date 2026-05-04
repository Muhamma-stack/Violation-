"""
AI SAMRAT - Content Analysis System
Main FastAPI application for Vercel deployment
"""

import os
from ai_samrat_analyzer import app

# Export the FastAPI app for Vercel
handler = app
