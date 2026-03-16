"""
Sistema de Notificações para Vexus CRM
Gerencia notificações em tempo real e alertas do sistema
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
    title: str
    message: str
    type: str
    user_id: Optional[str]
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotificationOut])
def get_notifications(
    skip: int = 0,
    limit: int = 10,
    user_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notifications for current user"""
    query = db.query(NotificationModel)
    
    if user_only:
        query = query.filter(
            (NotificationModel.user_id == current_user.id) | 
            (NotificationModel.user_id.is_(None))
        )
    
    # Sort by creation date (newest first)
    notifications = query.order_by(NotificationModel.created_at.desc()).offset(skip).limit(limit).all()
    
    return notifications

@router.post("/", response_model=NotificationOut, status_code=201)
def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification"""
    import uuid

    # If no user_id specified, it's a broadcast notification
    user_id = notification.user_id or current_user.id

    new_notification = NotificationModel(
        id=str(uuid.uuid4()),
        title=notification.title,
        message=notification.message,
        type=notification.type,
        user_id=user_id if notification.user_id else None,  # None = broadcast
        is_read=False,
        created_at=datetime.now()
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    
    return new_notification

    # Background task for real-time notifications (WebSocket, email, etc.)
    background_tasks.add_task(send_notification_alert, new_notification)

    return NotificationOut.from_orm(new_notification)

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