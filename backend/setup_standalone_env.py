#!/usr/bin/env python3
"""
Setup script for GharMitra Standalone Environment
Creates .env file from template with secure keys
"""
import secrets
import os
from pathlib import Path

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(64)

def generate_encryption_key():
    """Generate a secure random encryption key"""
    return secrets.token_urlsafe(32)

def setup_env():
    """Create .env file from template"""
    backend_dir = Path(__file__).parent
    env_file = backend_dir / ".env"
    template_file = backend_dir / ".env.standalone"
    
    # Check if .env already exists
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env creation.")
            return
    
    # Read template
    if template_file.exists():
        template_content = template_file.read_text()
    else:
        # Create template content if file doesn't exist
        template_content = """# GharMitra Standalone Configuration

# Application
APP_NAME=GharMitra
API_VERSION=v1
ENVIRONMENT=production
DEBUG=False

# Server
HOST=0.0.0.0
PORT=8001

# Database (Local SQLite - Standalone)
DATABASE_URL=sqlite+aiosqlite:///./GharMitra.db
DATABASE_ECHO=False

# Security
SECRET_KEY={SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS
ALLOWED_ORIGINS=*

# Deployment Mode
DEPLOYMENT_MODE=standalone

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=./uploads

# Encryption Key
ENCRYPTION_KEY={ENCRYPTION_KEY}

# Email (Optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@GharMitra.local

# Payment Gateway (Optional)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_ENABLED=False
RAZORPAY_LOGO_URL=
RAZORPAY_CONVENIENCE_FEE_PERCENTAGE=2.0
RAZORPAY_CONVENIENCE_FEE_BEARER=member

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
"""
    
    # Generate secure keys
    secret_key = generate_secret_key()
    encryption_key = generate_encryption_key()
    
    # Replace placeholders
    env_content = template_content.replace("{SECRET_KEY}", secret_key)
    env_content = env_content.replace("{ENCRYPTION_KEY}", encryption_key)
    
    # Write .env file
    env_file.write_text(env_content)
    
    print("✅ .env file created successfully!")
    print(f"   Location: {env_file}")
    print("\n📝 Generated secure keys:")
    print(f"   SECRET_KEY: {secret_key[:20]}...")
    print(f"   ENCRYPTION_KEY: {encryption_key[:20]}...")
    print("\n✅ Standalone environment configured!")
    print("\nNext steps:")
    print("   1. Start backend: start_standalone.bat (Windows) or ./start_standalone.sh (Linux/Mac)")
    print("   2. Update mobile app IP in src/config/env.ts")
    print("   3. Start mobile app: npm start")

if __name__ == "__main__":
    setup_env()


