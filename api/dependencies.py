from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_db
from database import crud
from utils.security import verify_telegram_webapp_data, is_admin

async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get current user from Telegram Web App data"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Verify Telegram data
        data = verify_telegram_webapp_data(authorization)
        telegram_id = data['user']['id']
        
        # Get user from database
        user = await crud.get_user_by_telegram_id(db, telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_banned:
            raise HTTPException(status_code=403, detail="User is banned")
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

async def get_admin_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get admin user"""
    user = await get_current_user(authorization, db)
    if not is_admin(user.telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
