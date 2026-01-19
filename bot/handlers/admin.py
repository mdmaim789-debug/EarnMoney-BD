from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.database import AsyncSessionLocal
from database import crud
from database.models import WithdrawalStatus
from bot.keyboards.inline import get_admin_keyboard, get_withdrawal_action_keyboard, get_back_to_admin_keyboard
from utils.security import is_admin
from config.settings import settings

router = Router()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# Admin command
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ You don't have admin access.")
        return
    
    async with AsyncSessionLocal() as db:
        total_users = await crud.get_total_users(db)
        total_earned = await crud.get_total_earnings_paid(db)
        total_withdrawn = await crud.get_total_withdrawn(db)
        pending_withdrawals = await crud.get_pending_withdrawals(db)
    
    admin_text = f"""
🔐 <b>Admin Panel</b>

📊 <b>Statistics:</b>
👥 Total Users: {total_users}
💰 Total Earnings Paid: {total_earned}৳
💸 Total Withdrawn: {total_withdrawn}৳
⏳ Pending Withdrawals: {len(pending_withdrawals)}

Select an option:
"""
    await message.answer(admin_text, reply_markup=get_admin_keyboard())

# Callback handlers
@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    """Show admin panel"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.message.edit_reply_markup(reply_markup=get_admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals(callback: CallbackQuery):
    """Show pending withdrawals"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    async with AsyncSessionLocal() as db:
        withdrawals = await crud.get_pending_withdrawals(db)
    
    if not withdrawals:
        await callback.answer("✅ No pending withdrawals", show_alert=True)
        return
    
    text = "💸 <b>Pending Withdrawals:</b>\n\n"
    for w in withdrawals[:10]:  # Show first 10
        user = await crud.get_user_by_telegram_id(db, w.user_id)
        text += f"""
<b>ID:</b> {w.id}
<b>User:</b> {user.first_name} ({user.telegram_id})
<b>Amount:</b> {w.amount}৳
<b>Method:</b> {w.method.upper()}
<b>Account:</b> {w.account_number}
<b>Date:</b> {w.created_at.strftime('%Y-%m-%d %H:%M')}
"""
        text += "—————————————\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_admin_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("approve_withdrawal_"))
async def approve_withdrawal(callback: CallbackQuery):
    """Approve withdrawal"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    withdrawal_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as db:
        withdrawal = await db.get(Withdrawal, withdrawal_id)
        if not withdrawal:
            await callback.answer("❌ Withdrawal not found", show_alert=True)
            return
        
        user = await db.get(User, withdrawal.user_id)
        user.total_withdrawn += withdrawal.amount
        
        await crud.update_withdrawal_status(
            db, withdrawal, WithdrawalStatus.APPROVED, 
            callback.from_user.id, "Approved by admin"
        )
    
    await callback.answer("✅ Withdrawal approved!", show_alert=True)
    # Notify user via bot would go here

@router.callback_query(F.data.startswith("reject_withdrawal_"))
async def reject_withdrawal(callback: CallbackQuery):
    """Reject withdrawal"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    withdrawal_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as db:
        withdrawal = await db.get(Withdrawal, withdrawal_id)
        if not withdrawal:
            await callback.answer("❌ Withdrawal not found", show_alert=True)
            return
        
        # Return balance to user
        user = await db.get(User, withdrawal.user_id)
        user.balance += withdrawal.amount
        
        await crud.update_withdrawal_status(
            db, withdrawal, WithdrawalStatus.REJECTED,
            callback.from_user.id, "Rejected by admin"
        )
    
    await callback.answer("❌ Withdrawal rejected", show_alert=True)

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Show statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    async with AsyncSessionLocal() as db:
        total_users = await crud.get_total_users(db)
        total_earned = await crud.get_total_earnings_paid(db)
        total_withdrawn = await crud.get_total_withdrawn(db)
    
    stats_text = f"""
📊 <b>System Statistics</b>

👥 <b>Total Users:</b> {total_users}
💰 <b>Total Earnings:</b> {total_earned}৳
💸 <b>Total Withdrawn:</b> {total_withdrawn}৳
💵 <b>Platform Balance:</b> {total_earned - total_withdrawn}৳

<b>Settings:</b>
Ad Earning: {settings.AD_EARNING}৳
Daily Limit: {settings.AD_DAILY_LIMIT} ads
Referral Bonus: {settings.REFERRAL_BONUS}৳
Min Withdrawal: {settings.MIN_WITHDRAWAL}৳
"""
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_back_to_admin_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Access denied", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 <b>Broadcast Message</b>\n\nSend the message you want to broadcast to all users:",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.answer()

@router.message(BroadcastState.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    """Process broadcast message"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await message.bot.send_message(user.telegram_id, message.text)
                success += 1
            except:
                failed += 1
    
    await message.answer(
        f"✅ Broadcast completed!\n\nSent: {success}\nFailed: {failed}",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()
