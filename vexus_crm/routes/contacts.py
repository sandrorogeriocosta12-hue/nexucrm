from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from vexus_crm.database import get_db
from vexus_crm.models import Contact as ContactModel, User
from vexus_crm.routes.auth import get_current_user

from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/contacts", tags=["Contacts"])


class ContactCreate(BaseModel):
    lead_id: Optional[str] = None
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    contact_type: Optional[str] = None


class ContactOut(BaseModel):
    id: str
    lead_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    contact_type: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ContactOut])
def list_contacts(
    skip: int = 0,
    limit: int = 10,
    lead_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all contacts, optionally filtered by lead_id"""
    query = db.query(ContactModel)
    if lead_id:
        query = query.filter(ContactModel.lead_id == lead_id)
    items = query.offset(skip).limit(limit).all()
    return [ContactOut(**item.__dict__) for item in items]


@router.post("/", response_model=ContactOut, status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new contact"""
    db_contact = ContactModel(
        lead_id=contact.lead_id,
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        role=contact.role,
        contact_type=contact.contact_type,
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return ContactOut(**db_contact.__dict__)


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific contact"""
    contact = db.query(ContactModel).get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactOut(**contact.__dict__)


@router.put("/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: str, contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a contact"""
    db_contact = db.query(ContactModel).get(contact_id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, field, value)
    db.commit()
    db.refresh(db_contact)
    return ContactOut(**db_contact.__dict__)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a contact"""
    contact = db.query(ContactModel).get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return None
