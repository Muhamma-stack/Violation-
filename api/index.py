"""
Vercel Serverless Function for AI SAMRAT
Handles both API and static file serving
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from ai_samrat_analyzer import app
from mangum import Mangum

# Create Mangum handler for Vercel
handler = Mangum(app)
