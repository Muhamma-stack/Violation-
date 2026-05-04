"""
AI SAMRAT - Content Analysis System
Step 1: Find keywords from PDF = terms that should NOT be in KSA school content (from ksa_policies.json).
Step 2: Run violation check only on those found keywords (context: educational vs promoting).
"""

import os
import re
import sys
import csv
import json
import shutil
import tempfile
from typing import List, Dict, Optional, Tuple

import PyPDF2
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICIES_PATH = os.path.join(BASE_DIR, "ksa_policies.json")


def load_policies() -> Dict:
    """Load policies and vocabulary from JSON config. No hardcoded keywords."""
    if os.path.isfile(POLICIES_PATH):
        try:
            with open(POLICIES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {POLICIES_PATH}: {e}")
    return {
        "educational_contexts": ["history of", "study of", "academic", "textbook", "chapter"],
        "prohibition_phrases": ["forbidden", "not allowed", "prohibited"],
        "policies": {}
    }


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', '"').replace('"', '"').replace("'", "'")
    return text.strip()


class AISamratAnalyzer:
    """
    Step 1: Find keywords from PDF (terms that should NOT be in KSA school content).
    Step 2: Run violation check on each found keyword.
    """

    def __init__(self):
        config = load_policies()
        self.policies = config.get("policies", {})
        self.educational_contexts = config.get("educational_contexts", [])
        self.prohibition_phrases = config.get("prohibition_phrases", [])

    def _get_prohibited_terms(self, policy_data: Dict) -> List[str]:
        """Terms that should NOT be in KSA school content (from config)."""
        return (
            policy_data.get("terms_not_allowed_in_ksa_schools")
            or policy_data.get("vocabulary")
            or policy_data.get("indicators")
            or []
        )

    def analyze_pdf(self, pdf_path: str) -> Tuple[List[Dict], int]:
        """
        Step 1: Find all keywords from PDF (prohibited terms that appear in the book).
        Step 2: Run violation check on each found keyword. Return only violations.
        """
        try:
            reader = PyPDF2.PdfReader(pdf_path)
        except Exception as e:
            print(f"Input error: {e}")
            return [], 0

        all_keyword_findings = []
        num_pages = len(reader.pages)

        for i in range(num_pages):
            page_num = i + 1
            page = reader.pages[i]
            raw_text = page.extract_text()
            clean_text = normalize_text(raw_text or "")
            if not clean_text:
                continue
            page_keywords = self._find_keywords_from_pdf(clean_text, page_num)
            all_keyword_findings.extend(page_keywords)

        violations = self._check_violations_on_keywords(all_keyword_findings)
        return self._deduplicate_findings(violations), num_pages

    def _find_keywords_from_pdf(self, text: str, page_num: int) -> List[Dict]:
        """
        Step 1: Find keywords from PDF = terms that should NOT be in KSA school content.
        Returns list of {keyword, page, category, context, policy_data} for each occurrence.
        """
        found = []
        text_lower = text.lower()

        for policy_name, policy_data in self.policies.items():
            prohibited_terms = self._get_prohibited_terms(policy_data)
            for term in prohibited_terms:
                term_lower = term.lower()
                if term_lower not in text_lower:
                    continue
                pattern = r'\b' + re.escape(term_lower) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    start = max(0, match.start() - 150)
                    end = min(len(text), match.end() + 150)
                    context = text[start:end].replace('\n', ' ').strip()
                    keyword_as_in_pdf = text[match.start():match.end()]
                    found.append({
                        'Keyword': keyword_as_in_pdf,
                        'Page': page_num,
                        'Category': policy_name,
                        'Context': context,
                        'policy_data': policy_data,
                    })
        return found

    def _check_violations_on_keywords(self, keyword_findings: List[Dict]) -> List[Dict]:
        """
        Step 2: Run violation check on each keyword found from PDF.
        Only returns findings that are actual violations (confidence >= 40).
        """
        violations = []
        for item in keyword_findings:
            is_violation, confidence = self._check_violation(item['Context'], item['Category'])
            if not is_violation or confidence < 40:
                continue
            policy_data = item['policy_data']
            violations.append({
                'Page': item['Page'],
                'Category': item['Category'],
                'Keyword': item['Keyword'],
                'Severity': policy_data.get('severity', 'High'),
                'Detail': f"Policy Breach: {policy_data.get('description', '')}",
                'Action': policy_data.get('action', 'Review'),
                'Confidence': confidence,
                'Violation': True,
            })
        return violations

    def _check_violation(self, context: str, policy_name: str) -> Tuple[bool, float]:
        """
        Check if this occurrence is a real violation (promoting) or e.g. educational/prohibition.
        Returns (is_violation, confidence).
        """
        context_lower = context.lower()
        confidence = 60.0

        if any(phrase in context_lower for phrase in self.educational_contexts):
            confidence -= 20.0
        if any(phrase in context_lower for phrase in self.prohibition_phrases):
            confidence -= 30.0

        confidence = max(0.0, min(100.0, confidence))
        is_violation = confidence >= 40
        return is_violation, confidence

    def _deduplicate_findings(self, findings: List[Dict]) -> List[Dict]:
        unique = []
        seen = set()
        for f in findings:
            key = (f['Page'], f['Category'], f['Keyword'].lower())
            if key not in seen:
                unique.append(f)
                seen.add(key)
        unique.sort(key=lambda x: (x['Page'], x['Severity'] == 'Medium'))
        return unique


def save_to_csv(findings: List[Dict], output_file: str):
    fieldnames = ['Page', 'Category', 'Keyword', 'Severity', 'Detail', 'Action']
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for f in findings:
            row = {k: f[k] for k in fieldnames}
            writer.writerow(row)
    print(f"Report saved: {output_file}")


# --- FastAPI app ---

app = FastAPI(
    title="AI SAMRAT Backend",
    max_request_size=None  # Unlimited file size
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def api_analyze_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        analyzer = AISamratAnalyzer()
        findings, total_pages = analyzer.analyze_pdf(tmp_path)
        return {
            "status": "success",
            "filename": file.filename,
            "total_pages": total_pages,
            "findings": findings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.get("/health")
async def health_check():
    return {"status": "online", "engine": "AI SAMRAT"}


@app.get("/")
async def serve_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/script.js")
async def serve_script():
    path = os.path.join(BASE_DIR, "script.js")
    if os.path.isfile(path):
        return FileResponse(path, media_type="application/javascript")
    raise HTTPException(status_code=404)


@app.get("/style.css")
async def serve_style():
    path = os.path.join(BASE_DIR, "style.css")
    if os.path.isfile(path):
        return FileResponse(path, media_type="text/css")
    raise HTTPException(status_code=404)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        print("AI SAMRAT Backend: http://127.0.0.1:8000")
        print("Open in browser: http://127.0.0.1:8000")
        uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        limit_concurrency=10
    )
    else:
        pdf_path = os.path.join(BASE_DIR, "9781663646842.pdf")
        output_file = os.path.join(BASE_DIR, "ksa_compliance_audit.csv")
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            print("To start server: python ai_samrat_analyzer.py server")
            return
        analyzer = AISamratAnalyzer()
        findings, total_pages = analyzer.analyze_pdf(pdf_path)
        print(f"Total pages in PDF: {total_pages}")
        save_to_csv(findings, output_file)


if __name__ == "__main__":
    main()
