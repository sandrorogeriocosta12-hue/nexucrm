from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, extract, case
from app.models import db, Lead, Deal, Proposal, User, Clinic, Activity
from app.sales_funnel import SalesFunnelManager, LeadStatus

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

@sales_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard comercial principal"""
    if current_user.role not in ['admin', 'sales_manager', 'sales']:
        return render_template('error.html', message="Acesso não autorizado"), 403

    # KPIs principais
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)

    # Leads do mês
    monthly_leads = Lead.query.filter(
        func.date(Lead.created_at) >= month_start
    ).count()

    # Negócios fechados
    closed_deals = Deal.query.filter(
        Deal.stage == 'closed_won',
        func.date(Deal.closed_at) >= month_start
    ).all()

    monthly_revenue = sum([deal.closed_value for deal in closed_deals])

    # Taxa de conversão
    contacted_leads = Lead.query.filter(
        Lead.status.in_(['contacted', 'qualified', 'proposal_sent', 'negotiation']),
        func.date(Lead.created_at) >= month_start
    ).count()

    conversion_rate = (len(closed_deals) / max(contacted_leads, 1)) * 100

    # Pipeline por estágio
    pipeline_stages = db.session.query(
        Deal.stage,
        func.count(Deal.id).label('count'),
        func.sum(Deal.value).label('value')
    ).filter(
        Deal.stage.notin_(['closed_won', 'closed_lost'])
    ).group_by(Deal.stage).all()

    # Top vendedores
    top_sellers = db.session.query(
        User.name,
        func.count(Deal.id).label('deals_count'),
        func.sum(Deal.closed_value).label('revenue')
    ).join(Deal, User.id == Deal.owner_id)\
    .filter(
        Deal.stage == 'closed_won',
        func.date(Deal.closed_at) >= month_start
    )\
    .group_by(User.id, User.name)\
    .order_by(func.sum(Deal.closed_value).desc())\
    .limit(5).all()

    # Leads por fonte
    leads_by_source = db.session.query(
        Lead.source,
        func.count(Lead.id).label('count'),
        func.sum(case([
            (Lead.status == 'closed_won', 1)
        ], else_=0)).label('converted')
    ).filter(
        func.date(Lead.created_at) >= month_start
    ).group_by(Lead.source).all()

    return render_template('sales/dashboard.html',
        monthly_leads=monthly_leads,
        monthly_revenue=monthly_revenue,
        conversion_rate=conversion_rate,
        pipeline_stages=pipeline_stages,
        top_sellers=top_sellers,
        leads_by_source=leads_by_source)

@sales_bp.route('/leads')
@login_required
def leads_list():
    """Lista de leads com filtros"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status')
    source = request.args.get('source')
    assigned_to = request.args.get('assigned_to')

    query = Lead.query

    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if assigned_to:
        query = query.filter(Lead.assigned_to == assigned_to)

    # Se for vendedor, mostrar apenas seus leads
    if current_user.role == 'sales':
        query = query.filter(Lead.assigned_to == current_user.id)

    leads = query.order_by(Lead.created_at.desc())\
        .paginate(page=page, per_page=per_page)

    return render_template('sales/leads.html', leads=leads)

@sales_bp.route('/pipeline')
@login_required
def pipeline():
    """Visualização do pipeline de vendas"""
    # Agrupar negócios por estágio
    deals_by_stage = {}

    stages = ['discovery', 'demo', 'proposal', 'negotiation', 'closed_won', 'closed_lost']

    for stage in stages:
        deals = Deal.query.filter_by(stage=stage).order_by(Deal.expected_close_date).all()

        deals_data = []
        for deal in deals:
            lead = Lead.query.get(deal.lead_id)
            owner = User.query.get(deal.owner_id)

            deals_data.append({
                'id': deal.id,
                'lead_name': lead.name if lead else 'N/A',
                'company': lead.company if lead else 'N/A',
                'value': float(deal.value),
                'probability': deal.probability * 100,
                'expected_close': deal.expected_close_date.strftime('%d/%m/%Y'),
                'owner': owner.name if owner else 'N/A',
                'days_in_stage': (datetime.utcnow() - deal.last_stage_change).days if deal.last_stage_change else 0
            })

        deals_by_stage[stage] = {
            'count': len(deals),
            'total_value': sum([d.value for d in deals]),
            'weighted_value': sum([d.value * d.probability for d in deals]),
            'deals': deals_data
        }

    return render_template('sales/pipeline.html', stages=deals_by_stage)

@sales_bp.route('/performance')
@login_required
def performance():
    """Relatório de performance da equipe"""
    # Se for gerente, ver toda a equipe
    if current_user.role in ['admin', 'sales_manager']:
        sellers = User.query.filter_by(role='sales').all()
    else:
        sellers = [current_user]

    performance_data = []

    for seller in sellers:
        # Estatísticas do mês
        month_start = datetime.utcnow().replace(day=1)

        leads_assigned = Lead.query.filter(
            Lead.assigned_to == seller.id,
            func.date(Lead.assigned_at) >= month_start
        ).count()

        deals_closed = Deal.query.filter(
            Deal.owner_id == seller.id,
            Deal.stage == 'closed_won',
            func.date(Deal.closed_at) >= month_start
        ).all()

        revenue = sum([deal.closed_value for deal in deals_closed])

        # Atividades do vendedor
        activities = Activity.query.filter(
            Activity.created_by == seller.id,
            func.date(Activity.created_at) >= month_start
        ).count()

        # Tempo médio de fechamento
        closed_deals_dates = [
            deal.closed_at for deal in deals_closed
            if deal.created_at and deal.closed_at
        ]

        avg_close_time = 0
        if closed_deals_dates:
            time_diffs = [
                (closed - created).days
                for created, closed in zip(
                    [deal.created_at for deal in deals_closed],
                    closed_deals_dates
                )
            ]
            avg_close_time = sum(time_diffs) / len(time_diffs)

        performance_data.append({
            'seller': seller.name,
            'leads_assigned': leads_assigned,
            'deals_closed': len(deals_closed),
            'revenue': revenue,
            'activities': activities,
            'avg_close_time': avg_close_time,
            'conversion_rate': (len(deals_closed) / max(leads_assigned, 1)) * 100
        })

    return render_template('sales/performance.html', performance=performance_data)

@sales_bp.route('/api/leads/chart')
@login_required
def leads_chart_data():
    """Dados para gráfico de leads ao longo do tempo"""
    days = request.args.get('days', 30, type=int)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query para contar leads por dia
    daily_leads = db.session.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count'),
        func.sum(case([
            (Lead.status == 'closed_won', 1)
        ], else_=0)).label('converted')
    ).filter(
        Lead.created_at >= start_date,
        Lead.created_at <= end_date
    ).group_by(func.date(Lead.created_at)).all()

    # Preparar dados para Chart.js
    dates = []
    counts = []
    converted = []

    for day in daily_leads:
        dates.append(day.date.strftime('%d/%m'))
        counts.append(day.count)
        converted.append(day.converted)

    return jsonify({
        'dates': dates,
        'counts': counts,
        'converted': converted
    })