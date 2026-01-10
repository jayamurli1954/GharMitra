"""
Development server runner
Run this file to start the FastAPI development server
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,  # Changed from 8000 to avoid conflict
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
