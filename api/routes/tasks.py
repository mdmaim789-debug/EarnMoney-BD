from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database.database import get_db
from database.models import User
from database import crud
from api.dependencies import get_current_user

router = APIRouter()

class TaskCompleteRequest(BaseModel):
    task_id: int

@router.get("/")
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active tasks"""
    tasks = await crud.get_active_tasks(db)
    
    result = []
    for task in tasks:
        completed = await crud.has_completed_task(db, current_user.id, task.id)
        
        # Check if task is still available
        is_available = True
        if task.max_completions and task.current_completions >= task.max_completions:
            is_available = False
        
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "type": task.task_type.value,
            "reward": task.reward,
            "url": task.url,
            "completed": completed,
            "available": is_available and not completed
        })
    
    return {"tasks": result}

@router.post("/complete")
async def complete_task(
    request: TaskCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Complete a task"""
    # Get task
    task = await crud.get_task_by_id(db, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.is_active:
        raise HTTPException(status_code=400, detail="Task is not active")
    
    # Check if already completed
    if await crud.has_completed_task(db, current_user.id, request.task_id):
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Check max completions
    if task.max_completions and task.current_completions >= task.max_completions:
        raise HTTPException(status_code=400, detail="Task limit reached")
    
    # Mark as completed
    await crud.complete_task(db, current_user.id, request.task_id)
    
    # Give reward
    await crud.update_user_balance(db, current_user, task.reward)
    
    # Create earning record
    await crud.create_earning(
        db=db,
        user_id=current_user.id,
        amount=task.reward,
        earning_type="task",
        description=f"Completed: {task.title}",
        task_id=task.id
    )
    
    return {
        "success": True,
        "earned": task.reward,
        "new_balance": current_user.balance,
        "task_title": task.title
    }
