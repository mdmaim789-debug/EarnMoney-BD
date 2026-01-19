from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from database.models import User
from database import crud
from api.dependencies import get_current_user
from config.settings import settings

router = APIRouter()

@router.post("/watch-ad")
async def watch_ad(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process ad watch earning"""
    # Reset daily counter if needed
    await crud.reset_daily_ads(db, current_user)
    
    # Check daily limit
    if current_user.ads_watched_today >= settings.AD_DAILY_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Daily limit reached. You can watch {settings.AD_DAILY_LIMIT} ads per day."
        )
    
    # Check cooldown
    if current_user.last_ad_watch:
        time_since_last = datetime.utcnow() - current_user.last_ad_watch
        if time_since_last.total_seconds() < settings.AD_COOLDOWN:
            remaining = settings.AD_COOLDOWN - int(time_since_last.total_seconds())
            raise HTTPException(
                status_code=400,
                detail=f"Please wait {remaining} seconds before watching next ad"
            )
    
    # Process earning
    current_user.last_ad_watch = datetime.utcnow()
    current_user.ads_watched_today += 1
    await crud.update_user_balance(db, current_user, settings.AD_EARNING)
    
    # Create earning record
    await crud.create_earning(
        db=db,
        user_id=current_user.id,
        amount=settings.AD_EARNING,
        earning_type="ad",
        description="Watched advertisement"
    )
    
    return {
        "success": True,
        "earned": settings.AD_EARNING,
        "new_balance": current_user.balance,
        "ads_watched_today": current_user.ads_watched_today,
        "remaining_today": settings.AD_DAILY_LIMIT - current_user.ads_watched_today
    }

@router.get("/history")
async def get_earning_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get earning history"""
    earnings = await crud.get_user_earnings(db, current_user.id)
    
    return {
        "earnings": [
            {
                "id": e.id,
                "amount": e.amount,
                "type": e.earning_type,
                "description": e.description,
                "created_at": e.created_at.isoformat()
            }
            for e in earnings
        ]
    }

@router.get("/stats")
async def get_earning_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get earning statistics"""
    today_earnings = await crud.get_today_earnings(db, current_user.id)
    await crud.reset_daily_ads(db, current_user)
    
    return {
        "balance": current_user.balance,
        "total_earned": current_user.total_earned,
        "total_withdrawn": current_user.total_withdrawn,
        "today_earnings": today_earnings,
        "ads_watched_today": current_user.ads_watched_today,
        "ads_remaining": settings.AD_DAILY_LIMIT - current_user.ads_watched_today
    }
