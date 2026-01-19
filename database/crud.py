from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Earning, Withdrawal, Task, TaskCompletion, WithdrawalStatus
import secrets

# ============ USER OPERATIONS ============

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, telegram_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None, referrer_id: int = None):
    referral_code = secrets.token_urlsafe(8)
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referral_code=referral_code,
        referrer_id=referrer_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user_balance(db: AsyncSession, user: User, amount: float):
    user.balance += amount
    user.total_earned += amount if amount > 0 else 0
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_referrals(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).where(User.referrer_id == user_id, User.is_active == True)
    )
    return result.scalars().all()

async def ban_user(db: AsyncSession, user: User, banned: bool):
    user.is_banned = banned
    await db.commit()
    return user

async def reset_daily_ads(db: AsyncSession, user: User):
    now = datetime.utcnow()
    if user.last_daily_reset.date() < now.date():
        user.ads_watched_today = 0
        user.last_daily_reset = now
        await db.commit()
    return user

# ============ EARNING OPERATIONS ============

async def create_earning(db: AsyncSession, user_id: int, amount: float, 
                        earning_type: str, description: str = None, task_id: int = None):
    earning = Earning(
        user_id=user_id,
        amount=amount,
        earning_type=earning_type,
        description=description,
        task_id=task_id
    )
    db.add(earning)
    await db.commit()
    await db.refresh(earning)
    return earning

async def get_user_earnings(db: AsyncSession, user_id: int, limit: int = 50):
    result = await db.execute(
        select(Earning)
        .where(Earning.user_id == user_id)
        .order_by(Earning.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_today_earnings(db: AsyncSession, user_id: int):
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.sum(Earning.amount))
        .where(
            and_(
                Earning.user_id == user_id,
                func.date(Earning.created_at) == today
            )
        )
    )
    return result.scalar() or 0.0

# ============ WITHDRAWAL OPERATIONS ============

async def create_withdrawal(db: AsyncSession, user_id: int, amount: float, 
                           method: str, account_number: str):
    withdrawal = Withdrawal(
        user_id=user_id,
        amount=amount,
        method=method,
        account_number=account_number
    )
    db.add(withdrawal)
    await db.commit()
    await db.refresh(withdrawal)
    return withdrawal

async def get_pending_withdrawals(db: AsyncSession):
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.status == WithdrawalStatus.PENDING)
        .order_by(Withdrawal.created_at.asc())
    )
    return result.scalars().all()

async def update_withdrawal_status(db: AsyncSession, withdrawal: Withdrawal, 
                                   status: WithdrawalStatus, admin_id: int, note: str = None):
    withdrawal.status = status
    withdrawal.approved_by = admin_id
    withdrawal.admin_note = note
    withdrawal.processed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(withdrawal)
    return withdrawal

async def get_user_withdrawals(db: AsyncSession, user_id: int, limit: int = 50):
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.user_id == user_id)
        .order_by(Withdrawal.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

# ============ TASK OPERATIONS ============

async def create_task(db: AsyncSession, title: str, description: str, 
                     task_type: str, reward: float, url: str, max_completions: int = None):
    task = Task(
        title=title,
        description=description,
        task_type=task_type,
        reward=reward,
        url=url,
        max_completions=max_completions
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

async def get_active_tasks(db: AsyncSession):
    result = await db.execute(
        select(Task).where(Task.is_active == True)
    )
    return result.scalars().all()

async def get_task_by_id(db: AsyncSession, task_id: int):
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

async def update_task(db: AsyncSession, task: Task, **kwargs):
    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task

async def delete_task(db: AsyncSession, task: Task):
    await db.delete(task)
    await db.commit()

async def has_completed_task(db: AsyncSession, user_id: int, task_id: int):
    result = await db.execute(
        select(TaskCompletion).where(
            and_(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_id == task_id
            )
        )
    )
    return result.scalar_one_or_none() is not None

async def complete_task(db: AsyncSession, user_id: int, task_id: int):
    completion = TaskCompletion(user_id=user_id, task_id=task_id)
    db.add(completion)
    
    # Update task completion count
    task = await get_task_by_id(db, task_id)
    if task:
        task.current_completions += 1
    
    await db.commit()
    await db.refresh(completion)
    return completion

# ============ STATISTICS ============

async def get_total_users(db: AsyncSession):
    result = await db.execute(select(func.count(User.id)))
    return result.scalar()

async def get_total_earnings_paid(db: AsyncSession):
    result = await db.execute(select(func.sum(Earning.amount)))
    return result.scalar() or 0.0

async def get_total_withdrawn(db: AsyncSession):
    result = await db.execute(
        select(func.sum(Withdrawal.amount))
        .where(Withdrawal.status == WithdrawalStatus.APPROVED)
    )
    return result.scalar() or 0.0
