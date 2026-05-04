# Frontend se kaise chalayein (Run from frontend)

## Step 1: Backend start karein

Terminal mein project folder mein jao aur ye command chalao:

```bash
pip install PyPDF2 fastapi uvicorn
python ai_samrat_analyzer.py server
```

Aapko dikhega:
```
AI SAMRAT Backend: http://127.0.0.1:8000
Open in browser: http://127.0.0.1:8000
```

## Step 2: Browser mein kholo

Browser mein ye URL open karo:

**http://127.0.0.1:8000**

Backend khud hi frontend (index.html, script.js, style.css) serve karega.

## Step 3: PDF upload karein

1. "Upload PDF Book File" pe click karke ek PDF select karo  
2. "AI SAMRAT - Analyze Book Content" button pe click karo  
3. File backend pe upload hogi, `ai_samrat_analyzer.py` run hoga  
4. Results same page pe table mein dikhenge (Total issues, High/Medium/Low, pagination, Excel download)

## Summary

- **Backend:** `python ai_samrat_analyzer.py server` → http://127.0.0.1:8000  
- **Frontend:** Browser mein http://127.0.0.1:8000 open karo  
- **Flow:** File upload → Backend analyze karta hai → Result frontend pe show hota hai  

Agar backend band ho to frontend pe error aayega: "Make sure the backend is running: python ai_samrat_analyzer.py server"
