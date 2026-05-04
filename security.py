"""
Security configurations and utilities for AI SAMRAT
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
import re

# Security context for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# HTTP Bearer for token authentication
security = HTTPBearer(auto_error=False)

class SecurityManager:
    """Manages security operations for the application."""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        
        # File upload security
        self.allowed_extensions = {'.pdf'}
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", 1048576000))  # 1000MB (1GB)
        
        # Rate limiting
        self.rate_limits = {
            "upload": {"requests": 2, "window": 60},  # 2 uploads per minute
            "analyze": {"requests": 10, "window": 60},  # 10 analyses per minute
            "default": {"requests": 100, "window": 60}  # 100 requests per minute
        }
        
        # Input validation patterns
        self.filename_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        self.text_pattern = re.compile(r'^[\w\s\-\.\,\:\;\!\?\(\)\[\]\"\'\/\\@#$%^&*+=<>\n\r\t]+$')
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[dict]:
        """Verify JWT token and return payload."""
        if credentials is None:
            return None
        
        try:
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def validate_file_upload(self, filename: str, file_size: int, file_content: bytes) -> bool:
        """Validate uploaded file for security."""
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not allowed. Allowed types: {self.allowed_extensions}"
            )
        
        # Check file size
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
            )
        
        # Check filename
        if not self.filename_pattern.match(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename format"
            )
        
        # Check file content (basic PDF signature check)
        if not file_content.startswith(b'%PDF'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format"
            )
        
        return True
    
    def sanitize_input(self, text: str, max_length: int = 10000) -> str:
        """Sanitize user input text."""
        if not text:
            return ""
        
        # Check length
        if len(text) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long. Maximum length: {max_length} characters"
            )
        
        # Basic pattern validation
        if not self.text_pattern.match(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid characters in input"
            )
        
        # Remove potentially dangerous content
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def check_rate_limit(self, client_ip: str, endpoint: str, redis_client=None) -> bool:
        """Check if client has exceeded rate limit."""
        if not redis_client:
            return True  # Skip rate limiting if Redis is not available
        
        limit_config = self.rate_limits.get(endpoint, self.rate_limits["default"])
        key = f"rate_limit:{client_ip}:{endpoint}"
        
        # Simple sliding window implementation
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - limit_config["window"]
        
        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_requests = redis_client.zcard(key)
        
        if current_requests >= limit_config["requests"]:
            return False
        
        # Add current request
        redis_client.zadd(key, {str(current_time): current_time})
        redis_client.expire(key, limit_config["window"])
        
        return True
    
    def get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token."""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token."""
        return secrets.compare_digest(token, session_token)

# Global security manager instance
security_manager = SecurityManager()

# Security headers middleware
def add_security_headers(response):
    """Add security headers to HTTP response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response

# Input validation decorators
def validate_pdf_upload(func):
    """Decorator to validate PDF uploads."""
    async def wrapper(*args, **kwargs):
        # Add validation logic here
        return await func(*args, **kwargs)
    return wrapper

def sanitize_text_input(max_length: int = 10000):
    """Decorator to sanitize text input."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Add sanitization logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator
