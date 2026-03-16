"""
Sistema de Relatórios e Analytics para Vexus CRM
Gera relatórios sobre leads, campanhas e performance
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

from vexus_crm.database import get_db
from vexus_crm.models import User, Lead, Campaign
from vexus_crm.routes.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Modelos Pydantic
class AnalyticsSummary(BaseModel):
    total_leads: int
    total_campaigns: int
    conversion_rate: float
    active_campaigns: int
    leads_by_status: Dict[str, int]
    leads_by_source: Dict[str, int]
    campaigns_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]

class ReportRequest(BaseModel):
    report_type: str  # leads, campaigns, performance
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    report_type: str
    generated_at: datetime
    date_range: Dict[str, datetime]
    data: Dict[str, Any]
    summary: Dict[str, Any]

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall analytics summary"""

    # Leads statistics
    total_leads = db.query(Lead).count()

    # Count leads by status
    leads_by_status = {}
    status_query = db.query(Lead.status, Lead.id).all()
    for status, _ in status_query:
        leads_by_status[status] = leads_by_status.get(status, 0) + 1

    # Count leads by source
    leads_by_source = {}
    source_query = db.query(Lead.source, Lead.id).all()
    for source, _ in source_query:
        if source:
            leads_by_source[source] = leads_by_source.get(source, 0) + 1

    # Campaigns statistics
    total_campaigns = db.query(Campaign).count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == "active").count()

    # Count campaigns by status
    campaigns_by_status = {}
    campaign_status_query = db.query(Campaign.status, Campaign.id).all()
    for status, _ in campaign_status_query:
        campaigns_by_status[status] = campaigns_by_status.get(status, 0) + 1

    # Calculate conversion rate (simplified)
    qualified_leads = leads_by_status.get('qualified', 0) + leads_by_status.get('converted', 0)
    conversion_rate = (qualified_leads / total_leads * 100) if total_leads > 0 else 0

    # Recent activity (last 10 leads and campaigns)
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(5).all()
    recent_campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(5).all()

    recent_activity = []

    for lead in recent_leads:
        recent_activity.append({
            "type": "lead",
            "id": lead.id,
            "title": f"Lead: {lead.name}",
            "description": f"New lead from {lead.source or 'unknown source'}",
            "timestamp": lead.created_at.isoformat(),
            "status": lead.status
        })

    for campaign in recent_campaigns:
        recent_activity.append({
            "type": "campaign",
            "id": campaign.id,
            "title": f"Campaign: {campaign.name}",
            "description": campaign.description or "New campaign created",
            "timestamp": campaign.created_at.isoformat(),
            "status": campaign.status
        })

    # Sort recent activity by timestamp
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activity = recent_activity[:10]  # Keep only 10 most recent

    return AnalyticsSummary(
        total_leads=total_leads,
        total_campaigns=total_campaigns,
        conversion_rate=round(conversion_rate, 2),
        active_campaigns=active_campaigns,
        leads_by_status=leads_by_status,
        leads_by_source=leads_by_source,
        campaigns_by_status=campaigns_by_status,
        recent_activity=recent_activity
    )

@router.post("/reports", response_model=ReportResponse)
def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate detailed reports"""

    # Set default date range (last 30 days)
    date_to = request.date_to or datetime.now()
    date_from = request.date_from or (date_to - timedelta(days=30))

    report_data = {}
    summary = {}

    if request.report_type == "leads":
        # Leads report
        leads_query = db.query(Lead).filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to
        )

        # Apply filters
        if request.filters:
            if request.filters.get("status"):
                leads_query = leads_query.filter(Lead.status == request.filters["status"])
            if request.filters.get("source"):
                leads_query = leads_query.filter(Lead.source == request.filters["source"])

        leads = leads_query.all()

        # Group by date
        leads_by_date = {}
        for lead in leads:
            date_key = lead.created_at.date().isoformat()
            if date_key not in leads_by_date:
                leads_by_date[date_key] = []
            leads_by_date[date_key].append({
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "status": lead.status,
                "source": lead.source,
                "created_at": lead.created_at.isoformat()
            })

        report_data = {
            "leads_by_date": leads_by_date,
            "total_leads": len(leads),
            "leads": [lead.__dict__ for lead in leads]
        }

        summary = {
            "period": f"{date_from.date()} to {date_to.date()}",
            "total_leads": len(leads),
            "avg_daily_leads": round(len(leads) / (date_to - date_from).days, 2) if (date_to - date_from).days > 0 else 0
        }

    elif request.report_type == "campaigns":
        # Campaigns report
        campaigns_query = db.query(Campaign).filter(
            Campaign.created_at >= date_from,
            Campaign.created_at <= date_to
        )

        if request.filters and request.filters.get("status"):
            campaigns_query = campaigns_query.filter(Campaign.status == request.filters["status"])

        campaigns = campaigns_query.all()

        report_data = {
            "campaigns": [campaign.__dict__ for campaign in campaigns],
            "total_campaigns": len(campaigns),
            "total_budget": sum(campaign.budget or 0 for campaign in campaigns)
        }

        summary = {
            "period": f"{date_from.date()} to {date_to.date()}",
            "total_campaigns": len(campaigns),
            "total_budget": report_data["total_budget"],
            "avg_budget": round(report_data["total_budget"] / len(campaigns), 2) if campaigns else 0
        }

    elif request.report_type == "performance":
        # Performance report combining leads and campaigns
        leads = db.query(Lead).filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to
        ).all()

        campaigns = db.query(Campaign).filter(
            Campaign.created_at >= date_from,
            Campaign.created_at <= date_to
        ).all()

        # Calculate KPIs
        total_leads = len(leads)
        active_campaigns = len([c for c in campaigns if c.status == "active"])
        conversion_rate = calculate_conversion_rate(leads)

        # Leads by status
        status_counts = {}
        for lead in leads:
            status_counts[lead.status] = status_counts.get(lead.status, 0) + 1

        report_data = {
            "kpis": {
                "total_leads": total_leads,
                "active_campaigns": active_campaigns,
                "conversion_rate": conversion_rate,
                "leads_by_status": status_counts
            },
            "leads": [lead.__dict__ for lead in leads],
            "campaigns": [campaign.__dict__ for campaign in campaigns]
        }

        summary = {
            "period": f"{date_from.date()} to {date_to.date()}",
            "performance_score": calculate_performance_score(total_leads, active_campaigns, conversion_rate),
            "recommendations": generate_recommendations(total_leads, active_campaigns, conversion_rate)
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

    return ReportResponse(
        report_type=request.report_type,
        generated_at=datetime.now(),
        date_range={"from": date_from, "to": date_to},
        data=report_data,
        summary=summary
    )

@router.get("/charts/leads-timeline")
def get_leads_timeline(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leads data for timeline chart"""
    date_from = datetime.now() - timedelta(days=days)

    leads = db.query(Lead).filter(Lead.created_at >= date_from).all()

    # Group by date
    timeline_data = {}
    for lead in leads:
        date_key = lead.created_at.date().isoformat()
        if date_key not in timeline_data:
            timeline_data[date_key] = 0
        timeline_data[date_key] += 1

    return {
        "timeline": timeline_data,
        "total_period": len(leads),
        "avg_daily": round(len(leads) / days, 2)
    }

@router.get("/charts/conversion-funnel")
def get_conversion_funnel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversion funnel data"""
    leads = db.query(Lead).all()

    funnel_data = {
        "total": len(leads),
        "new": len([l for l in leads if l.status == "new"]),
        "contacted": len([l for l in leads if l.status == "contacted"]),
        "qualified": len([l for l in leads if l.status == "qualified"]),
        "converted": len([l for l in leads if l.status in ["converted", "customer"]])
    }

    return funnel_data

# Utility functions
def calculate_conversion_rate(leads):
    """Calculate conversion rate from leads data"""
    if not leads:
        return 0

    converted = len([l for l in leads if l.status in ["qualified", "converted", "customer"]])
    return round((converted / len(leads)) * 100, 2)

def calculate_performance_score(total_leads, active_campaigns, conversion_rate):
    """Calculate overall performance score (0-100)"""
    # Simple scoring algorithm
    leads_score = min(total_leads / 10, 10)  # Max 10 points for leads
    campaigns_score = min(active_campaigns * 2, 10)  # Max 10 points for campaigns
    conversion_score = min(conversion_rate / 2, 10)  # Max 10 points for conversion

    return round(leads_score + campaigns_score + conversion_score, 1)

def generate_recommendations(total_leads, active_campaigns, conversion_rate):
    """Generate AI-powered recommendations"""
    recommendations = []

    if total_leads < 50:
        recommendations.append("Considere aumentar seus esforços de geração de leads")
    elif total_leads > 200:
        recommendations.append("Excelente volume de leads - foque na qualificação")

    if active_campaigns < 2:
        recommendations.append("Crie mais campanhas ativas para aumentar o engajamento")
    elif active_campaigns > 10:
        recommendations.append("Avalie a performance das campanhas existentes")

    if conversion_rate < 20:
        recommendations.append("Melhore o processo de qualificação de leads")
    elif conversion_rate > 50:
        recommendations.append("Ótima taxa de conversão - mantenha as boas práticas")

    if not recommendations:
        recommendations.append("Continue com as estratégias atuais - performance sólida")

    return recommendations