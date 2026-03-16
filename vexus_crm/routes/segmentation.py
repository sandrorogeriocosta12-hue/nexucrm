"""
API de Segmentação de Prospects para Vexus CRM
Segmenta leads baseado em critérios inteligentes e ML básico
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import statistics

from vexus_crm.database import get_db
from vexus_crm.models import User, Lead
from vexus_crm.routes.auth import get_current_user

router = APIRouter(prefix="/segmentation", tags=["Prospect Segmentation"])

# Modelos Pydantic
class SegmentationCriteria(BaseModel):
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    status: Optional[List[str]] = None
    source: Optional[List[str]] = None
    company_size: Optional[str] = None  # small, medium, large
    budget_range: Optional[str] = None  # low, medium, high
    interest_level: Optional[str] = None  # low, medium, high
    date_range: Optional[Dict[str, datetime]] = None

class SegmentationResult(BaseModel):
    segment_name: str
    criteria: Dict[str, Any]
    lead_count: int
    leads: List[Dict[str, Any]]
    avg_score: float
    conversion_potential: str  # high, medium, low
    recommendations: List[str]

class ProspectProfile(BaseModel):
    lead_id: str
    score: int
    segment: str
    priority: str  # high, medium, low
    next_action: str
    estimated_value: Optional[float] = None
    conversion_probability: float

@router.post("/segment", response_model=List[SegmentationResult])
def create_segments(
    criteria: SegmentationCriteria,
    segment_name: str = "Custom Segment",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create custom lead segments based on criteria"""

    # Build query
    query = db.query(Lead)

    # Apply filters
    if criteria.status:
        query = query.filter(Lead.status.in_(criteria.status))

    if criteria.source:
        query = query.filter(Lead.source.in_(criteria.source))

    if criteria.min_score is not None:
        query = query.filter(Lead.lead_score >= criteria.min_score)

    if criteria.max_score is not None:
        query = query.filter(Lead.lead_score <= criteria.max_score)

    if criteria.date_range:
        if criteria.date_range.get("from"):
            query = query.filter(Lead.created_at >= criteria.date_range["from"])
        if criteria.date_range.get("to"):
            query = query.filter(Lead.created_at <= criteria.date_range["to"])

    leads = query.all()

    if not leads:
        return []

    # Calculate segment metrics
    scores = [lead.lead_score for lead in leads if lead.lead_score]
    avg_score = statistics.mean(scores) if scores else 0

    # Determine conversion potential
    conversion_potential = "low"
    if avg_score >= 80:
        conversion_potential = "high"
    elif avg_score >= 60:
        conversion_potential = "medium"

    # Generate recommendations
    recommendations = generate_segment_recommendations(leads, avg_score, conversion_potential)

    # Convert leads to dict format
    leads_data = []
    for lead in leads:
        leads_data.append({
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "status": lead.status,
            "source": lead.source,
            "lead_score": lead.lead_score,
            "phase": lead.phase,
            "created_at": lead.created_at.isoformat() if lead.created_at else None
        })

    result = SegmentationResult(
        segment_name=segment_name,
        criteria=criteria.dict(),
        lead_count=len(leads),
        leads=leads_data,
        avg_score=round(avg_score, 2),
        conversion_potential=conversion_potential,
        recommendations=recommendations
    )

    return [result]

@router.get("/auto-segments", response_model=List[SegmentationResult])
def get_auto_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get automatically generated segments based on lead data"""

    leads = db.query(Lead).all()

    if not leads:
        return []

    segments = []

    # Segment 1: High-value prospects
    high_value = [l for l in leads if (l.lead_score or 0) >= 80 and l.status in ["qualified", "contacted"]]
    if high_value:
        segments.append(create_segment_result(
            "High-Value Prospects",
            high_value,
            "High-priority leads with strong conversion potential"
        ))

    # Segment 2: New leads needing attention
    new_leads = [l for l in leads if l.status == "new" and (l.created_at or datetime.min) >= datetime.now() - timedelta(days=7)]
    if new_leads:
        segments.append(create_segment_result(
            "New Leads (Last 7 days)",
            new_leads,
            "Fresh leads requiring immediate follow-up"
        ))

    # Segment 3: Cold leads
    cold_leads = [l for l in leads if (l.lead_score or 0) < 40 and l.status != "lost"]
    if cold_leads:
        segments.append(create_segment_result(
            "Cold Leads",
            cold_leads,
            "Leads needing re-engagement or nurturing"
        ))

    # Segment 4: Enterprise prospects
    enterprise = [l for l in leads if l.company and any(term in (l.company.lower() or "") for term in ["ltda", "s.a", "group", "corp"])]
    if enterprise:
        segments.append(create_segment_result(
            "Enterprise Prospects",
            enterprise,
            "Large company prospects with high potential value"
        ))

    return segments

@router.get("/prospect/{lead_id}", response_model=ProspectProfile)
def get_prospect_profile(
    lead_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed prospect profile with scoring and recommendations"""

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Calculate prospect score (0-100)
    score = calculate_prospect_score(lead)

    # Determine segment
    segment = get_prospect_segment(lead, score)

    # Determine priority
    priority = "low"
    if score >= 80:
        priority = "high"
    elif score >= 60:
        priority = "medium"

    # Next action recommendation
    next_action = get_next_action(lead, score, priority)

    # Conversion probability (simplified ML prediction)
    conversion_probability = min(score / 100, 0.95)  # Max 95%

    # Estimated value (simplified)
    estimated_value = estimate_lead_value(lead)

    return ProspectProfile(
        lead_id=lead_id,
        score=score,
        segment=segment,
        priority=priority,
        next_action=next_action,
        estimated_value=estimated_value,
        conversion_probability=round(conversion_probability, 2)
    )

@router.post("/bulk-score")
def bulk_score_leads(
    lead_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Score multiple leads and update their scores"""

    updated_leads = []

    for lead_id in lead_ids:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            # Calculate new score
            new_score = calculate_prospect_score(lead)

            # Update lead score
            lead.lead_score = new_score
            db.commit()

            updated_leads.append({
                "id": lead_id,
                "name": lead.name,
                "old_score": lead.lead_score,
                "new_score": new_score
            })

    return {
        "updated_count": len(updated_leads),
        "leads": updated_leads
    }

# Utility functions
def calculate_prospect_score(lead) -> int:
    """Calculate prospect score based on multiple factors"""

    score = 50  # Base score

    # Status factor
    status_weights = {
        "qualified": 30,
        "contacted": 20,
        "new": 10,
        "lost": -20,
        "converted": 40
    }
    score += status_weights.get(lead.status, 0)

    # Source factor
    source_weights = {
        "website": 10,
        "referral": 15,
        "social_media": 5,
        "paid_ads": 8,
        "organic_search": 12
    }
    score += source_weights.get(lead.source, 0)

    # Company factor
    if lead.company:
        if any(term in lead.company.lower() for term in ["ltda", "s.a", "group", "corp"]):
            score += 15  # Enterprise
        elif len(lead.company) > 20:
            score += 10  # Medium business
        else:
            score += 5   # Small business

    # Phone factor
    if lead.phone:
        score += 5

    # Interest/Budget factor
    if lead.interest:
        score += 10
    if lead.budget:
        score += 10

    # Time factor (newer leads get slight boost)
    if lead.created_at:
        days_old = (datetime.now() - lead.created_at).days
        if days_old < 7:
            score += 5
        elif days_old > 30:
            score -= 5

    return max(0, min(100, score))

def get_prospect_segment(lead, score: int) -> str:
    """Determine prospect segment"""

    if score >= 80:
        return "Champion"
    elif score >= 70:
        return "High Potential"
    elif score >= 60:
        return "Promising"
    elif score >= 40:
        return "Needs Nurturing"
    else:
        return "Low Priority"

def get_next_action(lead, score: int, priority: str) -> str:
    """Recommend next action for prospect"""

    if priority == "high":
        if lead.status == "new":
            return "Schedule immediate demo call"
        elif lead.status == "contacted":
            return "Send personalized proposal"
        else:
            return "Close the deal"

    elif priority == "medium":
        if not lead.phone:
            return "Request phone number for follow-up"
        else:
            return "Send educational content"

    else:  # low priority
        if (datetime.now() - (lead.created_at or datetime.min)).days > 30:
            return "Re-engage with special offer"
        else:
            return "Add to nurture campaign"

def estimate_lead_value(lead) -> Optional[float]:
    """Estimate lead value (simplified)"""

    base_value = 1000  # Base lead value

    # Company size multiplier
    if lead.company:
        company_name = lead.company.lower()
        if any(term in company_name for term in ["ltda", "s.a", "group", "corp"]):
            base_value *= 3  # Enterprise
        elif len(lead.company) > 20:
            base_value *= 2  # Medium
        else:
            base_value *= 1  # Small

    # Budget factor
    if lead.budget:
        if lead.budget > 50000:
            base_value *= 2
        elif lead.budget > 10000:
            base_value *= 1.5

    return round(base_value, 2)

def create_segment_result(name: str, leads: List, description: str) -> SegmentationResult:
    """Create segmentation result from lead list"""

    scores = [calculate_prospect_score(lead) for lead in leads]
    avg_score = statistics.mean(scores) if scores else 0

    conversion_potential = "low"
    if avg_score >= 80:
        conversion_potential = "high"
    elif avg_score >= 60:
        conversion_potential = "medium"

    leads_data = []
    for lead in leads:
        leads_data.append({
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "status": lead.status,
            "source": lead.source,
            "lead_score": calculate_prospect_score(lead),
            "phase": lead.phase,
            "created_at": lead.created_at.isoformat() if lead.created_at else None
        })

    return SegmentationResult(
        segment_name=name,
        criteria={"auto_generated": True, "description": description},
        lead_count=len(leads),
        leads=leads_data,
        avg_score=round(avg_score, 2),
        conversion_potential=conversion_potential,
        recommendations=generate_segment_recommendations(leads, avg_score, conversion_potential)
    )

def generate_segment_recommendations(leads, avg_score, potential):
    """Generate recommendations for segment"""

    recommendations = []

    if potential == "high":
        recommendations.append("Priorize estes leads para contato imediato")
        recommendations.append("Prepare propostas personalizadas")
        recommendations.append("Agende demonstrações para esta semana")

    elif potential == "medium":
        recommendations.append("Envie conteúdo educativo e cases de sucesso")
        recommendations.append("Agende follow-ups semanais")
        recommendations.append("Ofereça trials gratuitos")

    else:  # low
        recommendations.append("Adicione à campanha de nutrição por email")
        recommendations.append("Re-engage com ofertas especiais")
        recommendations.append("Considere remarketing nas redes sociais")

    if avg_score < 50:
        recommendations.append("Melhore a qualificação inicial dos leads")

    if len(leads) > 20:
        recommendations.append("Considere segmentar ainda mais este grupo")

    return recommendations