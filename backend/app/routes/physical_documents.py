"""
Physical Documents Checklist API Routes
Manages metadata for physically stored documents (no file storage)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.utils.encryption import encrypt, decrypt
from app.dependencies import get_current_user, get_current_admin_user
from app.models.user import UserResponse
from app.models_db import User, Flat

router = APIRouter(prefix="/api/physical-documents", tags=["Physical Documents"])

# ============= REQUEST MODELS =============

class CreatePhysicalDocumentRequest(BaseModel):
    member_id: str
    document_type: str
    storage_location: Optional[str] = None
    verification_notes: Optional[str] = None

class VerifyDocumentRequest(BaseModel):
    verification_notes: Optional[str] = None

class UpdateDocumentRequest(BaseModel):
    storage_location: Optional[str] = None
    verification_notes: Optional[str] = None

# ============= RESPONSE MODELS =============

class PhysicalDocumentResponse(BaseModel):
    id: str
    society_id: int
    member_id: int
    flat_id: int
    document_type: str
    submitted: bool
    submission_date: Optional[str]
    verified: bool
    verified_by: Optional[int]
    verified_by_name: Optional[str]
    verification_date: Optional[str]
    storage_location: Optional[str]
    verification_notes: Optional[str]
    created_at: str
    updated_at: str

# ============= HELPER FUNCTIONS =============

async def log_document_access(
    db: AsyncSession,
    document_id: Optional[str],
    accessed_by: int,
    access_type: str,
    request: Request
):
    """Log document access for audit trail."""
    try:
        await db.execute(
            text("""
                INSERT INTO document_access_logs 
                (document_id, document_type, accessed_by, access_type, ip_address, user_agent)
                VALUES (:document_id, 'physical', :accessed_by, :access_type, :ip_address, :user_agent)
            """),
            {
                "document_id": document_id,
                "accessed_by": accessed_by,
                "access_type": access_type,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get('user-agent')
            }
        )
        await db.commit()
    except Exception as e:
        print(f"Error logging access: {e}")

def encrypt_sensitive_fields(data: dict, use_encryption: bool = True) -> dict:
    """Encrypt sensitive fields before storing in database."""
    if not use_encryption:
        return data
    
    encrypted_data = data.copy()
    
    # Encrypt storage_location if present
    if data.get('storage_location'):
        encrypted_data['storage_location_encrypted'] = encrypt(data['storage_location'])
        encrypted_data['storage_location'] = None  # Clear plaintext
    
    # Encrypt verification_notes if present
    if data.get('verification_notes'):
        encrypted_data['verification_notes_encrypted'] = encrypt(data['verification_notes'])
        encrypted_data['verification_notes'] = None  # Clear plaintext
    
    return encrypted_data

def decrypt_sensitive_fields(row: dict) -> dict:
    """Decrypt sensitive fields when retrieving from database."""
    decrypted = dict(row)
    
    # Decrypt storage_location
    if row.get('storage_location_encrypted'):
        try:
            decrypted['storage_location'] = decrypt(row['storage_location_encrypted'])
        except:
            decrypted['storage_location'] = None
    
    # Decrypt verification_notes
    if row.get('verification_notes_encrypted'):
        try:
            decrypted['verification_notes'] = decrypt(row['verification_notes_encrypted'])
        except:
            decrypted['verification_notes'] = None
    
    return decrypted

# ============= API ENDPOINTS =============

@router.get("/{member_id}", response_model=List[PhysicalDocumentResponse])
async def get_physical_documents(
    member_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all physical documents checklist for a member.
    Returns only metadata, NOT actual document files.
    """
    try:
        # Convert member_id to int
        try:
            member_id_int = int(member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid member ID")
        
        # Verify user has permission to view this member's documents
        result = await db.execute(
            select(User).where(User.id == member_id_int)
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # TODO: Add permission check - user must be admin of this society or the member themselves
        
        # Fetch documents checklist
        result = await db.execute(
            text("""
                SELECT 
                  pdc.*,
                  u.name as verified_by_name
                FROM physical_documents_checklist pdc
                LEFT JOIN users u ON pdc.verified_by = u.id
                WHERE pdc.member_id = :member_id
                ORDER BY pdc.document_type
            """),
            {"member_id": member_id_int}
        )
        
        rows = result.fetchall()
        columns = result.keys()
        
        # Decrypt sensitive fields
        documents = []
        for row in rows:
            doc_dict = dict(zip(columns, row))
            doc = decrypt_sensitive_fields(doc_dict)
            doc['submitted'] = bool(doc.get('submitted', 0))
            doc['verified'] = bool(doc.get('verified', 0))
            documents.append(PhysicalDocumentResponse(**doc))
        
        # Log access
        await log_document_access(db, None, int(current_user.id), 'view', request)
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=PhysicalDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_physical_document(
    data: CreatePhysicalDocumentRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a physical document as submitted.
    Does NOT upload any files - only creates a checklist entry.
    """
    try:
        # Validate document type
        valid_types = ['aadhaar', 'pan', 'passport', 'driving_license', 
                      'rent_agreement', 'sale_deed', 'electricity_bill', 
                      'water_bill', 'other']
        
        if data.document_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Convert member_id to int
        try:
            member_id_int = int(data.member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid member ID")
        
        # Get member details
        result = await db.execute(
            select(User).where(User.id == member_id_int)
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Get flat_id from member (assuming member has flat_id or we need to get it from flats table)
        # For now, we'll need to get it from the user's apartment_number or flat relationship
        result = await db.execute(
            select(Flat).where(Flat.society_id == member.society_id).limit(1)
        )
        flat = result.scalar_one_or_none()
        
        if not flat:
            raise HTTPException(status_code=404, detail="Flat not found for member")
        
        flat_id = flat.id
        society_id = member.society_id if hasattr(member, 'society_id') else 1
        
        # Encrypt sensitive fields
        encrypted_data = encrypt_sensitive_fields({
            'storage_location': data.storage_location,
            'verification_notes': data.verification_notes
        })
        
        # Insert checklist entry
        result = await db.execute(
            text("""
                INSERT INTO physical_documents_checklist 
                (society_id, member_id, flat_id, document_type, submitted, submission_date,
                 storage_location, storage_location_encrypted, 
                 verification_notes, verification_notes_encrypted)
                VALUES (:society_id, :member_id, :flat_id, :document_type, 1, date('now'), 
                        :storage_location, :storage_location_encrypted, 
                        :verification_notes, :verification_notes_encrypted)
                RETURNING *
            """),
            {
                "society_id": society_id,
                "member_id": member_id_int,
                "flat_id": flat_id,
                "document_type": data.document_type,
                "storage_location": encrypted_data.get('storage_location'),
                "storage_location_encrypted": encrypted_data.get('storage_location_encrypted'),
                "verification_notes": encrypted_data.get('verification_notes'),
                "verification_notes_encrypted": encrypted_data.get('verification_notes_encrypted')
            }
        )
        
        row = result.fetchone()
        columns = result.keys()
        created_doc = dict(zip(columns, row))
        
        # Log access
        await log_document_access(db, created_doc['id'], int(current_user.id), 'create', request)
        
        # Decrypt before returning
        decrypted_doc = decrypt_sensitive_fields(created_doc)
        decrypted_doc['submitted'] = bool(decrypted_doc.get('submitted', 0))
        decrypted_doc['verified'] = bool(decrypted_doc.get('verified', 0))
        
        return PhysicalDocumentResponse(**decrypted_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{document_id}/verify", response_model=PhysicalDocumentResponse)
async def verify_physical_document(
    document_id: str,
    data: VerifyDocumentRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a physical document as verified after physical inspection.
    """
    try:
        # Check document exists
        result = await db.execute(
            text("SELECT society_id FROM physical_documents_checklist WHERE id = :document_id"),
            {"document_id": document_id}
        )
        doc = result.fetchone()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Encrypt verification notes if provided
        encrypted_notes = None
        if data.verification_notes:
            encrypted_notes = encrypt(data.verification_notes)
        
        # Update verification status
        await db.execute(
            text("""
                UPDATE physical_documents_checklist
                SET verified = 1,
                    verified_by = :verified_by,
                    verification_date = date('now'),
                    verification_notes = NULL,
                    verification_notes_encrypted = :verification_notes_encrypted,
                    updated_at = datetime('now')
                WHERE id = :document_id
            """),
            {
                "verified_by": int(current_user.id),
                "verification_notes_encrypted": encrypted_notes,
                "document_id": document_id
            }
        )
        await db.commit()
        
        # Get updated document with verified_by name
        result = await db.execute(
            text("""
                SELECT pdc.*, u.name as verified_by_name
                FROM physical_documents_checklist pdc
                LEFT JOIN users u ON pdc.verified_by = u.id
                WHERE pdc.id = :document_id
            """),
            {"document_id": document_id}
        )
        
        row = result.fetchone()
        columns = result.keys()
        updated_doc = dict(zip(columns, row))
        
        # Log access
        await log_document_access(db, document_id, int(current_user.id), 'verify', request)
        
        # Decrypt before returning
        decrypted_doc = decrypt_sensitive_fields(updated_doc)
        decrypted_doc['submitted'] = bool(decrypted_doc.get('submitted', 0))
        decrypted_doc['verified'] = bool(decrypted_doc.get('verified', 0))
        
        return PhysicalDocumentResponse(**decrypted_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{document_id}", response_model=PhysicalDocumentResponse)
async def update_physical_document(
    document_id: str,
    data: UpdateDocumentRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update storage location or verification notes for a document.
    """
    try:
        # Check document exists
        result = await db.execute(
            text("SELECT society_id FROM physical_documents_checklist WHERE id = :document_id"),
            {"document_id": document_id}
        )
        doc = result.fetchone()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Encrypt sensitive fields
        encrypted_data = encrypt_sensitive_fields({
            'storage_location': data.storage_location,
            'verification_notes': data.verification_notes
        })
        
        # Build update query dynamically
        updates = []
        params = {"document_id": document_id}
        
        if data.storage_location is not None:
            updates.append("storage_location = :storage_location")
            updates.append("storage_location_encrypted = :storage_location_encrypted")
            params["storage_location"] = encrypted_data.get('storage_location')
            params["storage_location_encrypted"] = encrypted_data.get('storage_location_encrypted')
        
        if data.verification_notes is not None:
            updates.append("verification_notes = :verification_notes")
            updates.append("verification_notes_encrypted = :verification_notes_encrypted")
            params["verification_notes"] = encrypted_data.get('verification_notes')
            params["verification_notes_encrypted"] = encrypted_data.get('verification_notes_encrypted')
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = datetime('now')")
        
        # Update document
        await db.execute(
            text(f"""
                UPDATE physical_documents_checklist
                SET {', '.join(updates)}
                WHERE id = :document_id
            """),
            params
        )
        await db.commit()
        
        # Fetch updated document
        result = await db.execute(
            text("""
                SELECT pdc.*, u.name as verified_by_name
                FROM physical_documents_checklist pdc
                LEFT JOIN users u ON pdc.verified_by = u.id
                WHERE pdc.id = :document_id
            """),
            {"document_id": document_id}
        )
        
        row = result.fetchone()
        columns = result.keys()
        updated_doc = dict(zip(columns, row))
        
        # Log access
        await log_document_access(db, document_id, int(current_user.id), 'update', request)
        
        # Decrypt before returning
        decrypted_doc = decrypt_sensitive_fields(updated_doc)
        decrypted_doc['submitted'] = bool(decrypted_doc.get('submitted', 0))
        decrypted_doc['verified'] = bool(decrypted_doc.get('verified', 0))
        
        return PhysicalDocumentResponse(**decrypted_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_physical_document(
    document_id: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a physical document checklist entry.
    Note: This only deletes the checklist entry, NOT the physical document.
    """
    try:
        # Check document exists
        result = await db.execute(
            text("SELECT society_id FROM physical_documents_checklist WHERE id = :document_id"),
            {"document_id": document_id}
        )
        doc = result.fetchone()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Log access before deleting
        await log_document_access(db, document_id, int(current_user.id), 'delete', request)
        
        # Delete document
        await db.execute(
            text("DELETE FROM physical_documents_checklist WHERE id = :document_id"),
            {"document_id": document_id}
        )
        await db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/society/{society_id}/summary")
async def get_society_documents_summary(
    society_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics of document submissions for a society.
    Useful for compliance reports.
    """
    try:
        try:
            society_id_int = int(society_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid society ID")
        
        result = await db.execute(
            text("""
                SELECT 
                  document_type,
                  COUNT(*) as total_count,
                  SUM(submitted) as submitted_count,
                  SUM(verified) as verified_count
                FROM physical_documents_checklist
                WHERE society_id = :society_id
                GROUP BY document_type
            """),
            {"society_id": society_id_int}
        )
        
        rows = result.fetchall()
        columns = result.keys()
        
        return [dict(zip(columns, row)) for row in rows]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")






