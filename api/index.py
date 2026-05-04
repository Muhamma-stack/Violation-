"""
Vercel Serverless Function for AI SAMRAT
Handles both API and static file serving
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the analyzer directly
from ai_samrat_analyzer import AISamratAnalyzer
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import shutil

# Create FastAPI app
app = FastAPI(title="AI SAMRAT Backend")
analyzer = AISamratAnalyzer()

@app.get("/")
async def root():
    """Serve the main HTML file"""
    parent_path = Path(__file__).parent.parent
    index_path = parent_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"message": "AI SAMRAT Backend Running"})

@app.get("/script.js")
async def serve_script():
    """Serve JavaScript file"""
    parent_path = Path(__file__).parent.parent
    script_path = parent_path / "script.js"
    if script_path.exists():
        return FileResponse(script_path, media_type="application/javascript")
    return JSONResponse({"error": "Script not found"}, status_code=404)

@app.get("/style.css")
async def serve_style():
    """Serve CSS file"""
    parent_path = Path(__file__).parent.parent
    style_path = parent_path / "style.css"
    if style_path.exists():
        return FileResponse(style_path, media_type="text/css")
    return JSONResponse({"error": "Style not found"}, status_code=404)

@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyze uploaded PDF file"""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return JSONResponse({"detail": "Only PDF files are supported"}, status_code=400)
    
    temp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        
        # Analyze the PDF
        findings, total_pages = analyzer.analyze_pdf(temp_path)
        
        return JSONResponse({
            "findings": findings,
            "total_pages": total_pages,
            "message": "Analysis complete"
        })
        
    except Exception as e:
        return JSONResponse({"detail": f"Analysis failed: {str(e)}"}, status_code=500)
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

# Export for Vercel
def handler(request):
    from mangum import Mangum
    mangum_handler = Mangum(app)
    return mangum_handler(request)
