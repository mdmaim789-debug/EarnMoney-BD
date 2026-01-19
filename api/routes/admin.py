from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database.database import get_db
from database.models import User, Task, TaskType, Withdrawal, WithdrawalStatus
from database import crud
from api.dependencies import get_admin_user
from config.settings import settings

router = APIRouter()

class CreateTaskRequest(BaseModel):
    title: str
    description: str
    task_type: str
    reward: float
    url: str
    max_completions: int = None

class UpdateTaskRequest(BaseModel):
    title: str = None
    description: str = None
    reward: float = None
    url: str = None
    is_active: bool = None
    max_completions: int = None

class BanUserRequest(BaseModel):
    user_id: int
    banned: bool

@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get admin statistics"""
    total_users = await crud.get_total_users(db)
    total_earned = await crud.get_total_earnings_paid(db)
    total_withdrawn = await crud.get_total_withdrawn(db)
    pending_withdrawals = await crud.get_pending_withdrawals(db)
    
    return {
        "total_users": total_users,
        "total_earned": total_earned,
        "total_withdrawn": total_withdrawn,
        "pending_withdrawals": len(pending_withdrawals),
        "platform_balance": total_earned - total_withdrawn
    }

@router.get("/users")
async def get_all_users(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users"""
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(100))
    users = result.scalars().all()
    
    return {
        "users": [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "balance": u.balance,
                "total_earned": u.total_earned,
                "is_banned": u.is_banned,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }

@router.post("/users/ban")
async def ban_user(
    request: BanUserRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Ban or unban a user"""
    user = await db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await crud.ban_user(db, user, request.banned)
    
    return {
        "success": True,
        "user_id": user.id,
        "banned": user.is_banned
    }

@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    task = await crud.create_task(
        db=db,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        reward=request.reward,
        url=request.url,
        max_completions=request.max_completions
    )
    
    return {
        "success": True,
        "task_id": task.id,
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "type": task.task_type.value,
            "reward": task.reward,
            "url": task.url
        }
    }

@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    request: UpdateTaskRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a task"""
    task = await crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    await crud.update_task(db, task, **update_data)
    
    return {
        "success": True,
        "task_id": task.id
    }

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task"""
    task = await crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await crud.delete_task(db, task)
    
    return {
        "success": True,
        "message": "Task deleted"
    }

@router.get("/withdrawals/pending")
async def get_pending_withdrawals(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending withdrawals"""
    withdrawals = await crud.get_pending_withdrawals(db)
    
    result = []
    for w in withdrawals:
        user = await db.get(User, w.user_id)
        result.append({
            "id": w.id,
            "amount": w.amount,
            "method": w.method,
            "account_number": w.account_number,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name
            },
            "created_at": w.created_at.isoformat()
        })
    
    return {"withdrawals": result}

@router.post("/withdrawals/{withdrawal_id}/approve")
async def approve_withdrawal(
    withdrawal_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a withdrawal"""
    withdrawal = await db.get(Withdrawal, withdrawal_id)
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    user = await db.get(User, withdrawal.user_id)
    user.total_withdrawn += withdrawal.amount
    
    await crud.update_withdrawal_status(
        db, withdrawal, WithdrawalStatus.APPROVED,
        current_user.telegram_id, "Approved by admin"
    )
    
    return {
        "success": True,
        "message": "Withdrawal approved"
    }

@router.post("/withdrawals/{withdrawal_id}/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a withdrawal"""
    withdrawal = await db.get(Withdrawal, withdrawal_id)
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    # Return balance to user
    user = await db.get(User, withdrawal.user_id)
    user.balance += withdrawal.amount
    
    await crud.update_withdrawal_status(
        db, withdrawal, WithdrawalStatus.REJECTED,
        current_user.telegram_id, "Rejected by admin"
    )
    
    return {
        "success": True,
        "message": "Withdrawal rejected and balance returned"
    }
