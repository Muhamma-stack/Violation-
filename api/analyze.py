"""
Vercel Serverless Function for PDF Analysis
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent))

from ai_samrat_analyzer import app
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum

# Create Mangum handler for Vercel
handler = Mangum(app)
