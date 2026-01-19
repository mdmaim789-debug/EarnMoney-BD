from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from database.database import AsyncSessionLocal
from database import crud
from bot.keyboards.inline import get_webapp_keyboard
from config.settings import settings

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        user = await crud.get_user_by_telegram_id(db, message.from_user.id)
        
        # Extract referrer ID from deep link
        referrer_id = None
        if message.text and len(message.text.split()) > 1:
            try:
                ref_code = message.text.split()[1]
                referrer = await crud.get_user_by_telegram_id(db, int(ref_code))
                if referrer:
                    referrer_id = referrer.id
            except ValueError:
                pass
        
        # Create new user if doesn't exist
        if not user:
            user = await crud.create_user(
                db=db,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                referrer_id=referrer_id
            )
            
            # Give referral bonus to referrer
            if referrer_id:
                referrer = await crud.get_user_by_telegram_id(db, int(ref_code))
                if referrer:
                    await crud.update_user_balance(db, referrer, settings.REFERRAL_BONUS)
                    await crud.create_earning(
                        db=db,
                        user_id=referrer.id,
                        amount=settings.REFERRAL_BONUS,
                        earning_type="referral",
                        description=f"Referral bonus from {user.first_name}"
                    )
            
            welcome_text = f"""
🎉 <b>স্বাগতম EarnMoney BD তে!</b>

আপনার রেজিস্ট্রেশন সফল হয়েছে।

👤 <b>User ID:</b> {user.telegram_id}
💰 <b>Balance:</b> {user.balance}৳

<b>কিভাবে টাকা আয় করবেন:</b>
✅ বিজ্ঞাপন দেখুন
✅ টাস্ক সম্পন্ন করুন
✅ বন্ধুদের রেফার করুন

নিচের বাটনে ক্লিক করে অ্যাপ ওপেন করুন 👇
"""
        else:
            # Check if user is banned
            if user.is_banned:
                await message.answer("❌ <b>আপনার অ্যাকাউন্ট নিষিদ্ধ করা হয়েছে।</b>")
                return
            
            welcome_text = f"""
👋 <b>আবার স্বাগতম, {user.first_name}!</b>

💰 <b>আপনার ব্যালেন্স:</b> {user.balance}৳
📊 <b>মোট আয়:</b> {user.total_earned}৳

নিচের বাটনে ক্লিক করে অ্যাপ ওপেন করুন 👇
"""
        
        await message.answer(
            welcome_text,
            reply_markup=get_webapp_keyboard()
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
📖 <b>সাহায্য - EarnMoney BD</b>

<b>কমান্ড সমূহ:</b>
/start - বট শুরু করুন
/help - সাহায্য দেখুন

<b>কিভাবে ব্যবহার করবেন:</b>
১। অ্যাপ ওপেন করুন
২। বিজ্ঞাপন দেখুন বা টাস্ক করুন
৩। টাকা আয় করুন
৪। ১০০৳ হলে উইথড্র করুন

<b>সাপোর্ট:</b>
যেকোনো সমস্যার জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।
"""
    await message.answer(help_text, reply_markup=get_webapp_keyboard())
