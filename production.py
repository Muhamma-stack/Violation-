"""
Production-ready AI SAMRAT Analyzer
Enhanced with security, logging, and monitoring
"""

import os
import sys
import logging
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import PyPDF2
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
UPLOAD_COUNT = Counter('file_uploads_total', 'Total file uploads', ['status'])
ANALYSIS_COUNT = Counter('pdf_analyses_total', 'Total PDF analyses', ['status'])

BASE_DIR = Path(__file__).parent
POLICIES_PATH = BASE_DIR / "ksa_policies.json"

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="AI SAMRAT Backend",
    description="Production-ready KSA Content Analysis System",
    version="1.0.0",
    max_request_size=None  # Unlimited file size
)

# Rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

# Static files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def load_policies() -> Dict:
    """Load policies and vocabulary from JSON config."""
    if POLICIES_PATH.exists():
        try:
            with open(POLICIES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load policies", path=str(POLICIES_PATH), error=str(e))
    
    logger.warning("Using default policies")
    return {
        "educational_contexts": ["history of", "study of", "academic", "textbook", "chapter"],
        "prohibition_phrases": ["forbidden", "not allowed", "prohibited"],
        "policies": {}
    }

def normalize_text(text: str) -> str:
    """Normalize text by fixing hyphens and extra spaces."""
    if not text:
        return ""
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', '"').replace('"', '"').replace("'", "'")
    return text.strip()

class ProductionAISamratAnalyzer:
    """Production-ready AI SAMRAT Analyzer with enhanced error handling."""
    
    def __init__(self):
        self.policies = load_policies()
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_samrat"
        self.temp_dir.mkdir(exist_ok=True)
        logger.info("Analyzer initialized", policies_count=len(self.policies.get("policies", {})))

    def analyze_pdf(self, pdf_path: Path) -> Tuple[List[Dict], int]:
        """Analyze PDF for policy violations."""
        findings = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                logger.info("Starting PDF analysis", path=str(pdf_path), pages=total_pages)
                
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        text = normalize_text(page.extract_text())
                        if not text:
                            continue
                            
                        page_findings = self._analyze_page_text(text, page_num)
                        findings.extend(page_findings)
                        
                    except Exception as e:
                        logger.error("Error processing page", page=page_num, error=str(e))
                        continue
                
                logger.info("PDF analysis completed", findings=len(findings), pages=total_pages)
                return findings, total_pages
                
        except Exception as e:
            logger.error("Failed to analyze PDF", path=str(pdf_path), error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to analyze PDF: {str(e)}")
    
    def _analyze_page_text(self, text: str, page_num: int) -> List[Dict]:
        """Analyze a single page of text."""
        findings = []
        text_lower = text.lower()
        
        # Check against policies
        for policy_name, policy_data in self.policies.get("policies", {}).items():
            keywords = policy_data.get("keywords", [])
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    findings.append({
                        "page": page_num,
                        "policy": policy_name,
                        "keyword": keyword,
                        "severity": policy_data.get("severity", "Medium"),
                        "action": policy_data.get("action", "Review content"),
                        "details": policy_data.get("details", f"Found {keyword} in content"),
                        "context": self._get_context(text, keyword)
                    })
        
        return findings
    
    def _get_context(self, text: str, keyword: str, context_size: int = 100) -> str:
        """Get context around keyword."""
        index = text.lower().find(keyword.lower())
        if index == -1:
            return ""
        
        start = max(0, index - context_size)
        end = min(len(text), index + len(keyword) + context_size)
        return text[start:end].strip()

# Initialize analyzer
analyzer = ProductionAISamratAnalyzer()

@app.post("/analyze")
@limiter.limit("10/minute")
async def api_analyze_pdf(request: Request, file: UploadFile = File(...)):
    """Analyze uploaded PDF file."""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if file.size > int(os.getenv("MAX_FILE_SIZE", 1048576000)):  # 1000MB
        raise HTTPException(status_code=413, detail="File too large")
    
    temp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = Path(tmp.name)
        
        logger.info("Analyzing PDF", filename=file.filename, size=file.size)
        UPLOAD_COUNT.labels(status="started").inc()
        
        # Analyze the PDF
        findings, total_pages = analyzer.analyze_pdf(temp_path)
        
        UPLOAD_COUNT.labels(status="completed").inc()
        ANALYSIS_COUNT.labels(status="completed").inc()
        
        logger.info("Analysis completed", filename=file.filename, findings=len(findings))
        
        return {
            "status": "success",
            "filename": file.filename,
            "total_pages": total_pages,
            "findings": findings,
            "violations_count": len(findings)
        }
        
    except Exception as e:
        UPLOAD_COUNT.labels(status="failed").inc()
        ANALYSIS_COUNT.labels(status="failed").inc()
        logger.error("Analysis failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temporary file
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "engine": "AI SAMRAT",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def serve_index():
    """Serve the main application."""
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found")

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        workers = int(os.getenv("WORKERS", 4))
        
        logger.info("Starting production server", host=host, port=port, workers=workers)
        
        uvicorn.run(
            "production:app",
            host=host,
            port=port,
            workers=workers,
            worker_class="gevent",
            limit_concurrency=1000,
            timeout_keep_alive=5,
            timeout_graceful_shutdown=30,
            access_log=True,
            log_level="info"
        )
    else:
        # Direct analysis mode
        pdf_path = BASE_DIR / "9781663646842.pdf"
        output_file = BASE_DIR / "ksa_compliance_audit.csv"
        
        if not pdf_path.exists():
            print(f"File not found: {pdf_path}")
            print("To start server: python production.py server")
            return
        
        findings, total_pages = analyzer.analyze_pdf(pdf_path)
        print(f"Total pages in PDF: {total_pages}")
        print(f"Total findings: {len(findings)}")
        
        # Save to CSV
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['page', 'policy', 'keyword', 'severity', 'action', 'details', 'context']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(findings)
        
        print(f"Report saved: {output_file}")

if __name__ == "__main__":
    main()
