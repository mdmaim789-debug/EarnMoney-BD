from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from database.models import User
from database import crud
from api.dependencies import get_current_user
from config.settings import settings

router = APIRouter()

@router.get("/stats")
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get referral statistics"""
    referrals = await crud.get_user_referrals(db, current_user.id)
    
    total_earned = len(referrals) * settings.REFERRAL_BONUS
    
    return {
        "referral_code": current_user.referral_code,
        "referral_link": f"https://t.me/EarnMoneyBD_bot?start={current_user.telegram_id}",
        "total_referrals": len(referrals),
        "active_referrals": len([r for r in referrals if r.is_active]),
        "total_earned": total_earned,
        "bonus_per_referral": settings.REFERRAL_BONUS
    }

@router.get("/list")
async def get_referral_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of referrals"""
    referrals = await crud.get_user_referrals(db, current_user.id)
    
    return {
        "referrals": [
            {
                "id": r.id,
                "username": r.username or "Unknown",
                "first_name": r.first_name,
                "is_active": r.is_active,
                "joined_at": r.created_at.isoformat(),
                "earned_bonus": settings.REFERRAL_BONUS
            }
            for r in referrals
        ]
    }
