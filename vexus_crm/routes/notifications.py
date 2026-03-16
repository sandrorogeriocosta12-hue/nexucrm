"""
Sistema de Notificações para Vexus CRM
Gerencia notificações em tempo real e alertas do sistema
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from vexus_crm.database import get_db
from vexus_crm.models import User, Notification as NotificationModel
from vexus_crm.routes.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Modelos Pydantic
class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"  # info, warning, error, success
    user_id: Optional[str] = None  # None = broadcast to all users

class NotificationOut(BaseModel):
    id: str
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    user_id: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None
    # Removido updated_at que pode causar problemas de serialização

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

@router.get("/", response_model=List[NotificationOut])
def get_notifications(
    skip: int = 0,
    limit: int = 10,
    user_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for current user"""
    try:
        query = db.query(NotificationModel)
        
        if user_only:
            query = query.filter(
                (NotificationModel.user_id == current_user.id) | 
                (NotificationModel.user_id.is_(None))
            )
        
        # Sort by creation date (newest first)
        notifications = query.order_by(NotificationModel.created_at.desc()).offset(skip).limit(limit).all()
        
        # Criar objetos NotificationOut manualmente para evitar problemas de serialização
        result = []
        for notification in notifications:
            result.append(NotificationOut(
                id=notification.id,
                title=notification.title,
                message=notification.message,
                type=notification.type,
                user_id=notification.user_id,
                is_read=notification.is_read,
                created_at=notification.created_at
            ))
        return result
    except Exception as e:
        import traceback, logging
        logging.exception("Erro ao listar notificações")
        # Em produção, mantenha a API responsiva retornando lista vazia
        return []

@router.post("/", response_model=NotificationOut, status_code=201)
def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification"""
    import uuid
    import logging

    try:
        # If no user_id specified, use current user (avoid NULL constraints)
        user_id = notification.user_id or current_user.id

        new_notification = NotificationModel(
            id=str(uuid.uuid4()),
            title=notification.title,
            message=notification.message,
            type=notification.type,
            user_id=user_id,
            is_read=False,
            created_at=datetime.now()
        )

        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        # Return explicit Pydantic model to satisfy response_model validation
        return NotificationOut(
            id=new_notification.id,
            title=new_notification.title,
            message=new_notification.message,
            type=new_notification.type,
            user_id=new_notification.user_id,
            is_read=new_notification.is_read,
            created_at=new_notification.created_at,
        )

    except Exception as e:
        logging.exception("Erro ao criar notificação")
        # Return structured error to aid debugging in production
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "details": str(e)
            },
        )

@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check if user can access this notification
    if notification.user_id and notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check if user can access this notification
    if notification.user_id and notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(notification)
    db.commit()
    return None

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    unread_count = db.query(NotificationModel).filter(
        ((NotificationModel.user_id == current_user.id) | (NotificationModel.user_id.is_(None))) &
        (NotificationModel.is_read == False)
    ).count()

    return {"unread_count": unread_count}

# Background task functions
async def send_notification_alert(notification):
    """Send notification alert (email, WebSocket, push notification, etc.)"""
    # Placeholder for notification delivery
    # In production: integrate with email service, WebSocket, push notifications
    print(f"📢 Notification sent: {notification.title}")

# Utility functions
async def create_system_notification(db: Session, title: str, message: str, notification_type: str = "info"):
    """Create a system-wide notification"""
    import uuid

    new_notification = NotificationModel(
        id=str(uuid.uuid4()),
        title=title,
        message=message,
        type=notification_type,
        user_id=None,  # Broadcast to all users
        is_read=False,
        created_at=datetime.now()
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification

async def create_user_notification(db: Session, user_id: str, title: str, message: str, notification_type: str = "info"):
    """Create a notification for specific user"""
    import uuid

    new_notification = NotificationModel(
        id=str(uuid.uuid4()),
        title=title,
        message=message,
        type=notification_type,
        user_id=user_id,
        is_read=False,
        created_at=datetime.now()
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification