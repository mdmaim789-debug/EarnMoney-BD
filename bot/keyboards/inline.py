from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config.settings import settings

def get_webapp_keyboard():
    """Get Web App keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Open App",
            web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/index.html")
        )]
    ])
    return keyboard

def get_admin_keyboard():
    """Get admin panel keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Users", callback_data="admin_users"),
            InlineKeyboardButton(text="💸 Withdrawals", callback_data="admin_withdrawals")
        ],
        [
            InlineKeyboardButton(text="📋 Tasks", callback_data="admin_tasks"),
            InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="admin_settings")
        ]
    ])
    return keyboard

def get_withdrawal_action_keyboard(withdrawal_id: int):
    """Get withdrawal action keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_withdrawal_{withdrawal_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_withdrawal_{withdrawal_id}")
        ]
    ])
    return keyboard

def get_back_to_admin_keyboard():
    """Get back to admin button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")]
    ])
    return keyboard
