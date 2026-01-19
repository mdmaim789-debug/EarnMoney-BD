from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from database.models import User
from api.dependencies import get_current_user

router = APIRouter()

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return {
        "id": current_user.id,
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "balance": current_user.balance,
        "total_earned": current_user.total_earned,
        "total_withdrawn": current_user.total_withdrawn,
        "referral_code": current_user.referral_code,
        "is_banned": current_user.is_banned,
        "created_at": current_user.created_at.isoformat()
    }

@router.get("/verify")
async def verify_auth(
    current_user: User = Depends(get_current_user)
):
    """Verify authentication"""
    return {
        "authenticated": True,
        "user_id": current_user.telegram_id
    }
