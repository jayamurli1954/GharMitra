"""
Legal documents API routes
Serves Terms of Service and Privacy Policy for both standalone and SaaS modes
"""
from fastapi import APIRouter, HTTPException, status
from pathlib import Path
from typing import Dict
import os

router = APIRouter()

# Path to legal documents (master copies)
LEGAL_DOCS_PATH = Path(__file__).parent.parent.parent / "legal"
TERMS_FILE = LEGAL_DOCS_PATH / "TERMS_OF_SERVICE.md"
PRIVACY_FILE = LEGAL_DOCS_PATH / "PRIVACY_POLICY.md"

# Current version of legal documents
LEGAL_VERSION = "1.0"
LAST_UPDATED = "2024-11-18T00:00:00Z"


def read_legal_document(file_path: Path) -> str:
    """Read legal document from file"""
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal document not found: {file_path.name}"
        )
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading legal document: {str(e)}"
        )


@router.get("/terms", tags=["Legal"])
async def get_terms_of_service() -> Dict[str, str]:
    """
    Get Terms of Service document
    
    Returns the full Terms of Service content in markdown format.
    Works for both standalone and SaaS deployment modes.
    """
    content = read_legal_document(TERMS_FILE)
    
    return {
        "content": content,
        "version": LEGAL_VERSION,
        "last_updated": LAST_UPDATED,
        "document_type": "terms_of_service"
    }


@router.get("/privacy", tags=["Legal"])
async def get_privacy_policy() -> Dict[str, str]:
    """
    Get Privacy Policy document
    
    Returns the full Privacy Policy content in markdown format.
    Works for both standalone and SaaS deployment modes.
    """
    content = read_legal_document(PRIVACY_FILE)
    
    return {
        "content": content,
        "version": LEGAL_VERSION,
        "last_updated": LAST_UPDATED,
        "document_type": "privacy_policy"
    }


@router.get("/version", tags=["Legal"])
async def get_legal_version() -> Dict[str, str]:
    """
    Get current version of legal documents
    
    Useful for checking if user needs to re-consent after document updates.
    """
    return {
        "version": LEGAL_VERSION,
        "last_updated": LAST_UPDATED,
        "terms_file_exists": TERMS_FILE.exists(),
        "privacy_file_exists": PRIVACY_FILE.exists()
    }






