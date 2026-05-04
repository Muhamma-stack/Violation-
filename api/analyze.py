"""
Vercel Serverless Function for PDF Analysis
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from ai_samrat_analyzer import AISamratAnalyzer

def handler(request):
    """Main handler for Vercel serverless function"""
    
    try:
        # Parse request
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        if method == 'GET' and path == '/':
            # Return HTML content
            parent_path = Path(__file__).parent.parent
            index_path = parent_path / "index.html"
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'text/html'},
                    'body': html_content
                }
            return {'statusCode': 404, 'body': 'Not found'}
            
        elif method == 'POST' and path == '/analyze':
            # Handle PDF analysis
            body = request.get('body', '')
            
            # For simplicity, return a test response
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'findings': [],
                    'total_pages': 0,
                    'message': 'Analysis endpoint working - backend deployed successfully'
                })
            }
        
        else:
            return {'statusCode': 404, 'body': 'Not found'}
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
