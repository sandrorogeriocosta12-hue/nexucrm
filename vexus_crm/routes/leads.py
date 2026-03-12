from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from vexus_crm.database import get_db
from vexus_crm.models import Lead as LeadModel

from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/leads", tags=["Leads"])


class LeadCreate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = "new"


class LeadOut(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    class Config:
        from_attributes = True


@router.get("/", response_model=List[LeadOut])
def list_leads(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(LeadModel)
    if status:
        query = query.filter(LeadModel.status == status)
    items = query.offset(skip).limit(limit).all()
    return items


@router.post("/", response_model=LeadOut, status_code=201)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = LeadModel(
        email=lead.email,
        name=lead.name,
        company=lead.company,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: str, lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = db.query(LeadModel).get(lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in lead.dict(exclude_unset=True).items():
        setattr(db_lead, field, value)
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.query(LeadModel).get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return None
