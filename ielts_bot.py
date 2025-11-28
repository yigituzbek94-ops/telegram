#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IELTS Pro Telegram Bot
Ro'yxatdan o'tish, majburiy kanal, AI chat funksiyalari bilan
"""

import os
import json
import random
import string
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Environment variables yuklash
load_dotenv()

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== KONFIGURATSIYA ====================

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8527617894:AAEP1UlgDy55gogspemMYKW7RUReXp7Y2NE')

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')

# Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyC7zcMNz5IbTsuIc9DqwCiucEe43El0RXQ')

# Admin ID lar (o'zingizning Telegram ID'ni qo'shing)
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip().isdigit()]

# Ma'lumotlar fayllari
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CODES_FILE = os.path.join(DATA_DIR, 'codes.json')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, 'chat_history.json')

# ==================== MA'LUMOTLAR BAZASI ====================

def ensure_data_dir():
    """Ma'lumotlar papkasini yaratish"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_data(filename: str, default: dict = None) -> dict:
    """JSON fayldan ma'lumot yuklash"""
    ensure_data_dir()
    if default is None:
        default = {}
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Fayl yuklashda xatolik: {e}")
    return default

def save_data(filename: str, data: dict):
    """Ma'lumotlarni JSON faylga saqlash"""
    ensure_data_dir()
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Faylga yozishda xatolik: {e}")

# ==================== SOZLAMALAR ====================

DEFAULT_SETTINGS = {
    "required_channels": [],  # Majburiy kanallar ro'yxati
    "welcome_message": "👋 IELTS Pro botiga xush kelibsiz!\n\n🎓 Biz sizga IELTS imtihoniga tayyorlanishda yordam beramiz.",
    "code_expiry_minutes": 10,  # Kod amal qilish muddati (daqiqa)
    "ai_enabled": True,
    "ai_provider": "gemini",  # gemini yoki openai
    "ai_system_prompt": "Siz IELTS imtihoniga tayyorlanish bo'yicha professional yordamchisiz. Foydalanuvchilarga IELTS bo'yicha yordam bering."
}

def get_settings() -> dict:
    """Sozlamalarni olish"""
    return load_data(SETTINGS_FILE, DEFAULT_SETTINGS)

def save_settings(settings: dict):
    """Sozlamalarni saqlash"""
    save_data(SETTINGS_FILE, settings)

# ==================== FOYDALANUVCHILAR ====================

def get_users() -> dict:
    """Foydalanuvchilarni olish"""
    return load_data(USERS_FILE, {"users": {}})

def save_users(users: dict):
    """Foydalanuvchilarni saqlash"""
    save_data(USERS_FILE, users)

def get_user(user_id: int) -> Optional[dict]:
    """Bitta foydalanuvchini olish"""
    users = get_users()
    return users["users"].get(str(user_id))

def save_user(user_id: int, user_data: dict):
    """Foydalanuvchini saqlash"""
    users = get_users()
    users["users"][str(user_id)] = user_data
    save_users(users)

def is_user_registered(user_id: int) -> bool:
    """Foydalanuvchi ro'yxatdan o'tganmi"""
    user = get_user(user_id)
    return user is not None and user.get("verified", False)

# ==================== KODLAR TIZIMI ====================

def get_codes() -> dict:
    """Kodlarni olish"""
    return load_data(CODES_FILE, {"codes": {}})

def save_codes(codes: dict):
    """Kodlarni saqlash"""
    save_data(CODES_FILE, codes)

def generate_code(user_id: int, telegram_username: str = None) -> str:
    """Yangi 6 ta raqamli kod yaratish"""
    settings = get_settings()
    codes = get_codes()
    
    # 6 ta raqamli kod yaratish
    code = ''.join(random.choices(string.digits, k=6))
    
    # Amal qilish muddati
    expiry = datetime.now() + timedelta(minutes=settings.get("code_expiry_minutes", 10))
    
    codes["codes"][code] = {
        "user_id": user_id,
        "telegram_username": telegram_username,
        "created_at": datetime.now().isoformat(),
        "expires_at": expiry.isoformat(),
        "used": False
    }
    
    save_codes(codes)
    logger.info(f"Yangi kod yaratildi: {code} - User: {user_id}")
    return code

def verify_code(code: str) -> Optional[dict]:
    """Kodni tekshirish"""
    codes = get_codes()
    
    if code not in codes["codes"]:
        return None
    
    code_data = codes["codes"][code]
    
    # Vaqti o'tganmi tekshirish
    expiry = datetime.fromisoformat(code_data["expires_at"])
    if datetime.now() > expiry:
        return None
    
    # Ishlatilganmi tekshirish
    if code_data["used"]:
        return None
    
    # Kodni ishlatilgan deb belgilash
    codes["codes"][code]["used"] = True
    codes["codes"][code]["used_at"] = datetime.now().isoformat()
    save_codes(codes)
    
    return code_data

def cleanup_expired_codes():
    """Eskirgan kodlarni tozalash"""
    codes = get_codes()
    now = datetime.now()
    
    to_delete = []
    for code, data in codes["codes"].items():
        expiry = datetime.fromisoformat(data["expires_at"])
        if now > expiry:
            to_delete.append(code)
    
    for code in to_delete:
        del codes["codes"][code]
    
    save_codes(codes)

# ==================== AI TIZIMI ====================

# OpenAI client
openai_client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client yaratildi")
    except Exception as e:
        logger.error(f"❌ OpenAI xatolik: {e}")

# Gemini model
gemini_model = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Model tanlash
        model_names = ['gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for model_name in model_names:
            try:
                test_model = genai.GenerativeModel(model_name)
                test_response = test_model.generate_content('test', generation_config={"max_output_tokens": 10})
                if test_response and hasattr(test_response, 'text'):
                    gemini_model = test_model
                    logger.info(f"✅ Gemini model yuklandi: {model_name}")
                    break
            except:
                continue
    except Exception as e:
        logger.error(f"❌ Gemini xatolik: {e}")

async def get_ai_response(user_message: str, user_id: int) -> str:
    """AI dan javob olish"""
    settings = get_settings()
    
    if not settings.get("ai_enabled", True):
        return "❌ AI yordamchi hozircha o'chirilgan."
    
    system_prompt = settings.get("ai_system_prompt", DEFAULT_SETTINGS["ai_system_prompt"])
    provider = settings.get("ai_provider", "gemini")
    
    # Chat history
    chat_history = load_data(CHAT_HISTORY_FILE, {"users": {}})
    user_history = chat_history.get("users", {}).get(str(user_id), [])
    
    try:
        # Avval Gemini dan foydalanish
        if provider == "gemini" and gemini_model:
            prompt = f"{system_prompt}\n\nFoydalanuvchi: {user_message}"
            response = gemini_model.generate_content(prompt)
            if response and hasattr(response, 'text') and response.text:
                answer = response.text
                
                # Historiyaga qo'shish
                user_history.append({"role": "user", "content": user_message})
                user_history.append({"role": "assistant", "content": answer})
                user_history = user_history[-20:]  # Oxirgi 20 ta xabar
                
                chat_history["users"][str(user_id)] = user_history
                save_data(CHAT_HISTORY_FILE, chat_history)
                
                return answer
        
        # OpenAI dan foydalanish
        if openai_client:
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(user_history[-10:])  # Oxirgi 10 ta xabar
            messages.append({"role": "user", "content": user_message})
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            # Historiyaga qo'shish
            user_history.append({"role": "user", "content": user_message})
            user_history.append({"role": "assistant", "content": answer})
            user_history = user_history[-20:]
            
            chat_history["users"][str(user_id)] = user_history
            save_data(CHAT_HISTORY_FILE, chat_history)
            
            return answer
        
        return "❌ AI yordamchi mavjud emas. Iltimos, keyinroq qayta urinib ko'ring."
        
    except Exception as e:
        logger.error(f"AI xatolik: {e}")
        return f"❌ Xatolik yuz berdi: {str(e)[:100]}"

# ==================== KANAL TEKSHIRUVI ====================

async def check_channel_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """Foydalanuvchi majburiy kanallarga a'zo ekanligini tekshirish"""
    settings = get_settings()
    required_channels = settings.get("required_channels", [])
    
    if not required_channels:
        return True, []
    
    not_subscribed = []
    
    for channel in required_channels:
        try:
            chat_id = channel.get("chat_id")
            if not chat_id:
                continue
                
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except Exception as e:
            logger.error(f"Kanal tekshirishda xatolik: {e}")
            # Xatolik bo'lsa ham davom etish
            continue
    
    return len(not_subscribed) == 0, not_subscribed

async def send_subscription_required(update: Update, context: ContextTypes.DEFAULT_TYPE, channels: list):
    """Obuna qilish kerakligi haqida xabar yuborish"""
    message = "⚠️ *Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:*\n\n"
    
    keyboard = []
    for channel in channels:
        message += f"📢 {channel.get('title', 'Kanal')}\n"
        keyboard.append([InlineKeyboardButton(
            f"📢 {channel.get('title', 'Kanalga o\'tish')}",
            url=channel.get('url', f"https://t.me/{channel.get('username', '')}")
        )])
    
    keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ==================== BOT HANDLERLARI ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni boshlash"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"Start: {user.first_name} ({user_id})")
    
    # Kanal obunasini tekshirish
    is_subscribed, not_subscribed = await check_channel_subscription(user_id, context)
    
    if not is_subscribed:
        await send_subscription_required(update, context, not_subscribed)
        return
    
    # Foydalanuvchini ro'yxatdan o'tkazish/yangilash
    user_data = get_user(user_id) or {}
    user_data.update({
        "user_id": user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "last_active": datetime.now().isoformat(),
        "verified": user_data.get("verified", False)
    })
    save_user(user_id, user_data)
    
    settings = get_settings()
    welcome = settings.get("welcome_message", DEFAULT_SETTINGS["welcome_message"])
    
    keyboard = [
        [KeyboardButton("🔑 Kod olish"), KeyboardButton("🤖 AI Yordamchi")],
        [KeyboardButton("📚 IELTS Materiallari"), KeyboardButton("📞 Aloqa")],
    ]
    
    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton("⚙️ Admin Panel")])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    message = f"{welcome}\n\n"
    message += f"👤 *{user.first_name}*, botdan foydalanish uchun tugmalardan birini tanlang.\n\n"
    message += "📝 Buyruqlar:\n"
    message += "/start - Botni boshlash\n"
    message += "/code - Ro'yxatdan o'tish kodi\n"
    message += "/ai <savol> - AI yordamchi\n"
    message += "/help - Yordam"
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ro'yxatdan o'tish kodini olish"""
    user = update.effective_user
    user_id = user.id
    
    # Kanal obunasini tekshirish
    is_subscribed, not_subscribed = await check_channel_subscription(user_id, context)
    
    if not is_subscribed:
        await send_subscription_required(update, context, not_subscribed)
        return
    
    # Kod yaratish
    code = generate_code(user_id, user.username)
    settings = get_settings()
    expiry_minutes = settings.get("code_expiry_minutes", 10)
    
    message = f"""🔑 *Sizning ro'yxatdan o'tish kodingiz:*

```
{code}
```

⏰ Kod {expiry_minutes} daqiqa ichida amal qiladi.

📋 Bu kodni saytda ro'yxatdan o'tish uchun kiriting.

⚠️ *Muhim:* Kodni boshqalarga bermang!"""
    
    keyboard = [[InlineKeyboardButton("🔄 Yangi kod olish", callback_data="new_code")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI yordamchi buyrug'i"""
    user_id = update.effective_user.id
    
    # Kanal obunasini tekshirish
    is_subscribed, not_subscribed = await check_channel_subscription(user_id, context)
    
    if not is_subscribed:
        await send_subscription_required(update, context, not_subscribed)
        return
    
    if not context.args:
        await update.message.reply_text(
            "🤖 *AI Yordamchi*\n\n"
            "Menga savol yuboring:\n"
            "/ai Sizning savolingiz\n\n"
            "Yoki shunchaki xabar yozing!",
            parse_mode='Markdown'
        )
        return
    
    question = " ".join(context.args)
    await process_ai_message(update, context, question)

async def process_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    """AI xabarni qayta ishlash"""
    user_id = update.effective_user.id
    
    wait_msg = await update.message.reply_text("🤔 O'ylamoqdaman...")
    
    try:
        answer = await get_ai_response(question, user_id)
        
        await wait_msg.delete()
        await update.message.reply_text(
            f"🤖 *AI Javob:*\n\n{answer}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"AI xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik: {str(e)[:100]}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    message = """📖 *IELTS Pro Bot Yordam*

🔑 *Ro'yxatdan o'tish:*
• /code yoki "🔑 Kod olish" - ro'yxatdan o'tish kodini olish
• Kodni saytga kiriting

🤖 *AI Yordamchi:*
• /ai <savol> - AI dan savol so'rash
• Yoki shunchaki xabar yozing

📚 *IELTS Materiallari:*
• Reading, Writing, Listening, Speaking bo'yicha materiallar

📞 *Aloqa:*
• @admin - Admin bilan bog'lanish

⚙️ *Admin buyruqlari:*
• /admin - Admin panel (faqat adminlar uchun)"""
    
    await update.message.reply_text(message, parse_mode='Markdown')

# ==================== ADMIN FUNKSIYALARI ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sizda admin huquqi yo'q!")
        return
    
    users = get_users()
    codes = get_codes()
    settings = get_settings()
    
    total_users = len(users.get("users", {}))
    active_codes = len([c for c in codes.get("codes", {}).values() if not c.get("used")])
    total_channels = len(settings.get("required_channels", []))
    
    message = f"""⚙️ *Admin Panel*

📊 *Statistika:*
• Foydalanuvchilar: {total_users}
• Faol kodlar: {active_codes}
• Majburiy kanallar: {total_channels}

🤖 *AI:*
• Holat: {'✅ Yoqilgan' if settings.get('ai_enabled') else '❌ O\'chirilgan'}
• Provider: {settings.get('ai_provider', 'gemini').upper()}"""
    
    keyboard = [
        [InlineKeyboardButton("📢 Kanallar", callback_data="admin_channels"),
         InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("🤖 AI sozlamalari", callback_data="admin_ai"),
         InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Majburiy kanal qo'shish"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin huquqi yo'q!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format: /addchannel @username Kanal nomi\n\n"
            "Misol: /addchannel @myChannel Mening Kanalim"
        )
        return
    
    channel_username = context.args[0]
    channel_title = " ".join(context.args[1:])
    
    # Kanal ma'lumotlarini olish
    try:
        chat = await context.bot.get_chat(channel_username)
        
        settings = get_settings()
        channels = settings.get("required_channels", [])
        
        # Mavjud emasligini tekshirish
        for ch in channels:
            if ch.get("chat_id") == chat.id:
                await update.message.reply_text("⚠️ Bu kanal allaqachon qo'shilgan!")
                return
        
        channels.append({
            "chat_id": chat.id,
            "username": chat.username,
            "title": channel_title or chat.title,
            "url": f"https://t.me/{chat.username}" if chat.username else None
        })
        
        settings["required_channels"] = channels
        save_settings(settings)
        
        await update.message.reply_text(
            f"✅ Kanal qo'shildi!\n\n"
            f"📢 {channel_title}\n"
            f"🔗 @{chat.username}"
        )
        
    except Exception as e:
        logger.error(f"Kanal qo'shishda xatolik: {e}")
        await update.message.reply_text(f"❌ Xatolik: {e}")

async def admin_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Majburiy kanalni o'chirish"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin huquqi yo'q!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Format: /removechannel @username")
        return
    
    channel_username = context.args[0].replace("@", "")
    
    settings = get_settings()
    channels = settings.get("required_channels", [])
    
    new_channels = [ch for ch in channels if ch.get("username") != channel_username]
    
    if len(new_channels) == len(channels):
        await update.message.reply_text("⚠️ Kanal topilmadi!")
        return
    
    settings["required_channels"] = new_channels
    save_settings(settings)
    
    await update.message.reply_text(f"✅ @{channel_username} kanali o'chirildi!")

async def admin_list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Majburiy kanallar ro'yxati"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin huquqi yo'q!")
        return
    
    settings = get_settings()
    channels = settings.get("required_channels", [])
    
    if not channels:
        await update.message.reply_text("📢 Majburiy kanallar yo'q.")
        return
    
    message = "📢 *Majburiy kanallar:*\n\n"
    for i, ch in enumerate(channels, 1):
        message += f"{i}. {ch.get('title')} (@{ch.get('username')})\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha foydalanuvchilarga xabar yuborish"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin huquqi yo'q!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Format: /broadcast Xabar matni")
        return
    
    message = " ".join(context.args)
    users = get_users()
    
    sent = 0
    failed = 0
    
    for uid in users.get("users", {}).keys():
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 *Admin xabari:*\n\n{message}",
                parse_mode='Markdown'
            )
            sent += 1
            await asyncio.sleep(0.1)  # Rate limit
        except Exception as e:
            failed += 1
    
    await update.message.reply_text(
        f"✅ Xabar yuborildi!\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Xatolik: {failed}"
    )

# ==================== CALLBACK HANDLER ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback querylarni boshqarish"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "check_subscription":
        is_subscribed, not_subscribed = await check_channel_subscription(user_id, context)
        
        if is_subscribed:
            await query.edit_message_text(
                "✅ Ajoyib! Siz barcha kanallarga obuna bo'lgansiz.\n\n"
                "/start buyrug'ini bosing!"
            )
        else:
            await send_subscription_required(update, context, not_subscribed)
    
    elif data == "new_code":
        user = update.effective_user
        code = generate_code(user_id, user.username)
        settings = get_settings()
        expiry_minutes = settings.get("code_expiry_minutes", 10)
        
        await query.edit_message_text(
            f"🔑 *Yangi ro'yxatdan o'tish kodingiz:*\n\n"
            f"```\n{code}\n```\n\n"
            f"⏰ Kod {expiry_minutes} daqiqa ichida amal qiladi.",
            parse_mode='Markdown'
        )
    
    elif data.startswith("admin_"):
        if user_id not in ADMIN_IDS:
            await query.answer("❌ Admin huquqi yo'q!", show_alert=True)
            return
        
        action = data.replace("admin_", "")
        
        if action == "channels":
            settings = get_settings()
            channels = settings.get("required_channels", [])
            
            message = "📢 *Majburiy kanallar:*\n\n"
            if not channels:
                message += "Hech qanday kanal yo'q.\n\n"
            else:
                for i, ch in enumerate(channels, 1):
                    message += f"{i}. {ch.get('title')} (@{ch.get('username')})\n"
            
            message += "\n📝 Buyruqlar:\n"
            message += "/addchannel @username Nomi - Kanal qo'shish\n"
            message += "/removechannel @username - Kanalni o'chirish"
            
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif action == "users":
            users = get_users()
            total = len(users.get("users", {}))
            
            message = f"👥 *Foydalanuvchilar:* {total}\n\n"
            
            # Oxirgi 10 ta
            user_list = list(users.get("users", {}).values())[-10:]
            for u in reversed(user_list):
                username = f"@{u.get('username')}" if u.get('username') else "—"
                message += f"• {u.get('first_name')} ({username})\n"
            
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif action == "ai":
            settings = get_settings()
            
            message = f"""🤖 *AI Sozlamalari*

• Holat: {'✅ Yoqilgan' if settings.get('ai_enabled') else '❌ O\'chirilgan'}
• Provider: {settings.get('ai_provider', 'gemini').upper()}
• Gemini: {'✅' if gemini_model else '❌'}
• OpenAI: {'✅' if openai_client else '❌'}"""
            
            keyboard = [
                [InlineKeyboardButton(
                    "❌ O'chirish" if settings.get('ai_enabled') else "✅ Yoqish",
                    callback_data="toggle_ai"
                )],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        
        elif action == "stats":
            users = get_users()
            codes = get_codes()
            
            total_users = len(users.get("users", {}))
            total_codes = len(codes.get("codes", {}))
            used_codes = len([c for c in codes.get("codes", {}).values() if c.get("used")])
            
            message = f"""📊 *Statistika*

👥 Foydalanuvchilar: {total_users}
🔑 Jami kodlar: {total_codes}
✅ Ishlatilgan: {used_codes}
⏳ Faol: {total_codes - used_codes}"""
            
            await query.edit_message_text(message, parse_mode='Markdown')
        
        elif action == "back":
            await admin_panel(update, context)
    
    elif data == "toggle_ai":
        if user_id not in ADMIN_IDS:
            return
        
        settings = get_settings()
        settings["ai_enabled"] = not settings.get("ai_enabled", True)
        save_settings(settings)
        
        status_text = "yoqildi" if settings['ai_enabled'] else "o'chirildi"
        await query.answer(f"AI {status_text}!")
        
        # Admin AI sahifasiga qaytish
        query.data = "admin_ai"
        await handle_callback(update, context)

# ==================== XABAR HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarlarni boshqarish"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text
    
    # Kanal obunasini tekshirish
    is_subscribed, not_subscribed = await check_channel_subscription(user_id, context)
    
    if not is_subscribed:
        await send_subscription_required(update, context, not_subscribed)
        return
    
    # Tugmalarni boshqarish
    if text == "🔑 Kod olish":
        await get_code(update, context)
    elif text == "🤖 AI Yordamchi":
        await update.message.reply_text(
            "🤖 *AI Yordamchi*\n\n"
            "Menga savol yuboring, men javob beraman!\n\n"
            "Misol: IELTS Writing Task 2 uchun maslahat bering",
            parse_mode='Markdown'
        )
    elif text == "📚 IELTS Materiallari":
        keyboard = [
            [InlineKeyboardButton("📖 Reading", callback_data="material_reading"),
             InlineKeyboardButton("✍️ Writing", callback_data="material_writing")],
            [InlineKeyboardButton("🎧 Listening", callback_data="material_listening"),
             InlineKeyboardButton("🗣 Speaking", callback_data="material_speaking")],
        ]
        await update.message.reply_text(
            "📚 *IELTS Materiallari*\n\n"
            "Qaysi bo'limni tanlaysiz?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    elif text == "📞 Aloqa":
        await update.message.reply_text(
            "📞 *Aloqa*\n\n"
            "📱 Admin: @admin\n"
            "📧 Email: info@example.com\n\n"
            "Savollaringiz bo'lsa, yozing!",
            parse_mode='Markdown'
        )
    elif text == "⚙️ Admin Panel":
        await admin_panel(update, context)
    else:
        # AI ga yuborish
        settings = get_settings()
        if settings.get("ai_enabled", True) and len(text) > 2:
            await process_ai_message(update, context, text)
        else:
            await update.message.reply_text(
                "Iltimos, tugmalardan birini tanlang yoki /help buyrug'ini ishlating."
            )

# ==================== MAIN ====================

async def run_bot():
    """Botni async ishga tushirish"""
    # Bot yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("code", get_code))
    application.add_handler(CommandHandler("ai", ai_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("addchannel", admin_add_channel))
    application.add_handler(CommandHandler("removechannel", admin_remove_channel))
    application.add_handler(CommandHandler("channels", admin_list_channels))
    application.add_handler(CommandHandler("broadcast", admin_broadcast))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Botni ishga tushirish
    logger.info("=" * 50)
    logger.info("🤖 IELTS Pro Bot ishga tushmoqda...")
    logger.info(f"📱 Token: {BOT_TOKEN[:20]}...")
    logger.info(f"🤖 OpenAI: {'✅' if openai_client else '❌'}")
    logger.info(f"🌟 Gemini: {'✅' if gemini_model else '❌'}")
    logger.info("=" * 50)
    
    # Initialize and run
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        logger.info("✅ Bot ishga tushdi! To'xtatish uchun Ctrl+C bosing.")
        
        # Bot ishlayotgan paytda kutish
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def main():
    """Botni ishga tushirish"""
    import time
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi!")
        return
    
    # Ma'lumotlar papkasini yaratish
    ensure_data_dir()
    
    # Eskirgan kodlarni tozalash
    cleanup_expired_codes()
    
    restart_count = 0
    max_restarts = 100
    
    while restart_count < max_restarts:
        try:
            logger.info("🚀 Bot ishga tushirilmoqda...")
            asyncio.run(run_bot())
            
        except KeyboardInterrupt:
            logger.info("⏹️ Bot to'xtatildi.")
            break
        except Exception as e:
            restart_count += 1
            logger.error(f"❌ Xatolik: {e}")
            logger.info(f"🔄 Qayta ishga tushirish ({restart_count})...")
            time.sleep(10)

if __name__ == '__main__':
    main()

