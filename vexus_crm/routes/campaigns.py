from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from vexus_crm.database import get_db
from vexus_crm.models import Campaign as CampaignModel
from pydantic import BaseModel

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "draft"
    launch_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None


class CampaignOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[str]
    launch_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True


@router.get("/", response_model=List[CampaignOut])
def list_campaigns(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(CampaignModel).offset(skip).limit(limit).all()


@router.post("/", response_model=CampaignOut, status_code=201)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    db_cam = CampaignModel(
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        launch_date=campaign.launch_date,
        end_date=campaign.end_date,
        budget=campaign.budget
    )
    db.add(db_cam)
    db.commit()
    db.refresh(db_cam)
    return db_cam


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    cam = db.query(CampaignModel).get(campaign_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return cam


@router.put("/{campaign_id}", response_model=CampaignOut)
def update_campaign(campaign_id: str, campaign: CampaignCreate, db: Session = Depends(get_db)):
    db_cam = db.query(CampaignModel).get(campaign_id)
    if not db_cam:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db_cam.name = campaign.name
    db_cam.status = campaign.status
    db.commit()
    db.refresh(db_cam)
    return db_cam


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    cam = db.query(CampaignModel).get(campaign_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(cam)
    db.commit()
    return None
