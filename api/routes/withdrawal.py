from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.database import get_db
from database.models import User
from database import crud
from api.dependencies import get_current_user
from config.settings import settings

router = APIRouter()

class WithdrawalRequest(BaseModel):
    amount: float
    method: str  # bkash, nagad, rocket
    account_number: str

@router.post("/request")
async def request_withdrawal(
    request: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Request a withdrawal"""
    # Validate amount
    if request.amount < settings.MIN_WITHDRAWAL:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum withdrawal amount is {settings.MIN_WITHDRAWAL}৳"
        )
    
    # Check balance
    if current_user.balance < request.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance"
        )
    
    # Validate method
    if request.method.lower() not in ['bkash', 'nagad', 'rocket']:
        raise HTTPException(
            status_code=400,
            detail="Invalid withdrawal method"
        )
    
    # Validate account number (11 digits for Bangladesh)
    if not request.account_number.isdigit() or len(request.account_number) != 11:
        raise HTTPException(
            status_code=400,
            detail="Invalid account number. Must be 11 digits."
        )
    
    # Deduct balance
    current_user.balance -= request.amount
    
    # Create withdrawal request
    withdrawal = await crud.create_withdrawal(
        db=db,
        user_id=current_user.id,
        amount=request.amount,
        method=request.method.lower(),
        account_number=request.account_number
    )
    
    return {
        "success": True,
        "withdrawal_id": withdrawal.id,
        "amount": withdrawal.amount,
        "method": withdrawal.method,
        "status": withdrawal.status.value,
        "message": "Withdrawal request submitted. Admin will review soon."
    }

@router.get("/history")
async def get_withdrawal_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get withdrawal history"""
    withdrawals = await crud.get_user_withdrawals(db, current_user.id)
    
    return {
        "withdrawals": [
            {
                "id": w.id,
                "amount": w.amount,
                "method": w.method,
                "account_number": w.account_number,
                "status": w.status.value,
                "admin_note": w.admin_note,
                "created_at": w.created_at.isoformat(),
                "processed_at": w.processed_at.isoformat() if w.processed_at else None
            }
            for w in withdrawals
        ]
    }

@router.get("/methods")
async def get_withdrawal_methods():
    """Get available withdrawal methods"""
    return {
        "methods": [
            {
                "id": "bkash",
                "name": "bKash",
                "icon": "💳",
                "min_amount": settings.MIN_WITHDRAWAL
            },
            {
                "id": "nagad",
                "name": "Nagad",
                "icon": "💰",
                "min_amount": settings.MIN_WITHDRAWAL
            },
            {
                "id": "rocket",
                "name": "Rocket",
                "icon": "🚀",
                "min_amount": settings.MIN_WITHDRAWAL
            }
        ]
    }
