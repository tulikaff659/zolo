import logging
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Environment variables orqali konfiguratsiya
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID environment variable is not set!")

# APK fayllar uchun papka
APK_FOLDER = "apk_files"
if not os.path.exists(APK_FOLDER):
    os.makedirs(APK_FOLDER, mode=0o777)
    logger.info(f"APK papkasi yaratildi: {APK_FOLDER}")

# Tugmalar ro'yxati
BUTTONS = {
    "betwinner": {"name": "Betwinner", "file": None},
    "1xbet": {"name": "1xBet", "file": None},
    "winwin": {"name": "WinWin", "file": None},
    "dbbet": {"name": "DBBet", "file": None},
    "megapari": {"name": "Mega Pari", "file": None},
    "888starz": {"name": "888Starz", "file": None},
    "goldpari": {"name": "GoldPari", "file": None},
    "lucypari": {"name": "LucyPari", "file": None}
}

# Saqlangan APK fayllarni yuklash
def load_existing_apks():
    loaded_count = 0
    for button_id in BUTTONS.keys():
        file_path = os.path.join(APK_FOLDER, f"{button_id}.apk")
        if os.path.exists(file_path):
            BUTTONS[button_id]["file"] = file_path
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"APK yuklandi: {button_id} - {file_size:.2f} MB")
            loaded_count += 1
    logger.info(f"Jami {loaded_count} ta APK fayl yuklandi")

# Botni ishga tushirishda mavjud APKlarni yuklash
load_existing_apks()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi - asosiy menyu"""
    try:
        keyboard = []
        
        # Tugmalarni yaratish
        for button_id, button_info in BUTTONS.items():
            if button_info["file"] and os.path.exists(button_info["file"]):
                keyboard.append([InlineKeyboardButton(
                    button_info["name"], 
                    callback_data=f"get_{button_id}"
                )])
        
        # Agar hech qanday APK mavjud bo'lmasa
        if not keyboard:
            await update.message.reply_text(
                "📱 <b>Yangilangan APK fayllar</b>\n\n"
                "Hozircha hech qanday APK fayl mavjud emas. Tez orada qo'shiladi!",
                parse_mode=ParseMode.HTML
            )
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📱 <b>Yangilangan APK fayllar</b>\n\n"
            "Quyidagi tugmalardan birini tanlab, so'nggi versiya APK faylini yuklab oling:",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Start funksiyasida xatolik: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugmalar bosilganda ishlaydi"""
    try:
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data.startswith("get_"):
            button_id = callback_data[4:]
            if button_id in BUTTONS and BUTTONS[button_id]["file"]:
                file_path = BUTTONS[button_id]["file"]
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as apk_file:
                            await query.message.reply_document(
                                document=apk_file,
                                filename=f"{button_id}.apk",
                                caption=f"✅ {BUTTONS[button_id]['name']} uchun so'nggi APK fayl"
                            )
                    except Exception as e:
                        logger.error(f"Fayl yuborishda xatolik: {e}")
                        await query.message.reply_text(
                            f"❌ APK faylni yuborishda xatolik: {str(e)}"
                        )
                else:
                    BUTTONS[button_id]["file"] = None
                    await query.message.reply_text(
                        "❌ APK fayl topilmadi. Admin yangilashi kerak."
                    )
    except Exception as e:
        logger.error(f"Button callbackda xatolik: {e}")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun yordam"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun!")
        return
    
    help_text = """
🔰 <b>Admin buyruqlari:</b>

/upload [tugma_nomi] - APK fayl yuklash
    Masalan: /upload betwinner

/list - Barcha tugmalar va ularning holati

/delete [tugma_nomi] - APK faylni o'chirish
    Masalan: /delete betwinner

/help - Bu yordam xabari

<b>Mavjud tugmalar:</b>
"""
    
    for button_id, button_info in BUTTONS.items():
        status = "✅ APK mavjud" if button_info["file"] and os.path.exists(button_info["file"]) else "❌ APK mavjud emas"
        help_text += f"• {button_info['name']} (@{button_id}) - {status}\n"
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha tugmalar ro'yxati"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun!")
        return
    
    text = "📋 <b>Tugmalar ro'yxati:</b>\n\n"
    for button_id, button_info in BUTTONS.items():
        if button_info["file"] and os.path.exists(button_info["file"]):
            file_size = os.path.getsize(button_info["file"]) / (1024 * 1024)
            text += f"✅ {button_info['name']} - {file_size:.2f} MB\n"
        else:
            text += f"❌ {button_info['name']} - APK mavjud emas\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def upload_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """APK fayl yuklash (faqat admin)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun!")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Tugma nomini kiriting!\n"
            "Masalan: /upload betwinner\n\n"
            f"Mavjud tugmalar: {', '.join(BUTTONS.keys())}"
        )
        return
    
    button_id = context.args[0].lower()
    
    if button_id not in BUTTONS:
        await update.message.reply_text(
            f"❌ Noto'g'ri tugma nomi!\n"
            f"Mavjud tugmalar: {', '.join(BUTTONS.keys())}"
        )
        return
    
    context.user_data['waiting_for_apk'] = button_id
    await update.message.reply_text(
        f"📤 {BUTTONS[button_id]['name']} uchun APK faylni yuboring.\n\n"
        f"Qabul qilinadigan fayl: .apk\n"
        f"Maksimal hajm: 50 MB"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yuborilgan hujjatlarni qabul qilish"""
    try:
        # Admin tekshirish
        if update.effective_user.id != ADMIN_ID:
            return
        
        # APK yuklash holatida tekshirish
        if 'waiting_for_apk' not in context.user_data:
            await update.message.reply_text(
                "❌ APK yuklash uchun avval /upload buyrug'ini kiriting!"
            )
            return
        
        button_id = context.user_data['waiting_for_apk']
        document = update.message.document
        
        if not document:
            await update.message.reply_text("❌ Hujjat topilmadi!")
            return
        
        file_name = document.file_name or "unknown.apk"
        
        # Fayl kengaytmasini tekshirish
        if not file_name.lower().endswith('.apk'):
            await update.message.reply_text(
                "❌ Faqat .apk fayllar qabul qilinadi!\n"
                f"Siz yuborgan fayl: {file_name}"
            )
            # Holatni tozalash
            del context.user_data['waiting_for_apk']
            return
        
        # Fayl hajmini tekshirish
        if document.file_size > 50 * 1024 * 1024:
            await update.message.reply_text(
                "❌ Fayl hajmi 50MB dan katta bo'lmasligi kerak!\n"
                f"Fayl hajmi: {document.file_size / (1024*1024):.2f} MB"
            )
            # Holatni tozalash
            del context.user_data['waiting_for_apk']
            return
        
        progress_msg = await update.message.reply_text(
            f"📥 APK yuklanmoqda...\n"
            f"Tugma: {BUTTONS[button_id]['name']}\n"
            f"Fayl: {file_name}\n"
            f"Hajm: {document.file_size / (1024*1024):.2f} MB"
        )
        
        try:
            # Faylni yuklab olish
            file = await context.bot.get_file(document.file_id)
            
            # Fayl yo'li
            file_path = os.path.join(APK_FOLDER, f"{button_id}.apk")
            
            # Eski fayl mavjud bo'lsa o'chirish
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Oldingi fayl o'chirildi: {file_path}")
            
            # Yangi faylni saqlash
            await file.download_to_drive(file_path)
            
            # Fayl saqlanganligini tekshirish
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                
                # Tugma ma'lumotlarini yangilash
                BUTTONS[button_id]["file"] = file_path
                
                # Holatni tozalash
                del context.user_data['waiting_for_apk']
                
                # Progress xabarni o'chirish
                await progress_msg.delete()
                
                await update.message.reply_text(
                    f"✅ <b>{BUTTONS[button_id]['name']} uchun APK muvaffaqiyatli yuklandi!</b>\n\n"
                    f"📁 Fayl: {file_name}\n"
                    f"📦 Hajm: {file_size / (1024*1024):.2f} MB",
                    parse_mode=ParseMode.HTML
                )
                
                logger.info(f"APK muvaffaqiyatli yuklandi: {button_id}")
            else:
                raise Exception("Fayl saqlanmadi!")
                
        except Exception as e:
            logger.error(f"Fayl yuklashda xatolik: {e}")
            await progress_msg.delete()
            await update.message.reply_text(
                f"❌ APK yuklashda xatolik:\n{str(e)}\n\n"
                f"Iltimos, qaytadan urinib ko'ring."
            )
            # Holatni tozalash
            if 'waiting_for_apk' in context.user_data:
                del context.user_data['waiting_for_apk']
            
    except Exception as e:
        logger.error(f"handle_document funksiyasida xatolik: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")

async def delete_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """APK faylni o'chirish"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun!")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Tugma nomini kiriting!\n"
            "Masalan: /delete betwinner"
        )
        return
    
    button_id = context.args[0].lower()
    
    if button_id not in BUTTONS:
        await update.message.reply_text("❌ Bunday tugma mavjud emas!")
        return
    
    if BUTTONS[button_id]["file"] and os.path.exists(BUTTONS[button_id]["file"]):
        try:
            os.remove(BUTTONS[button_id]["file"])
            BUTTONS[button_id]["file"] = None
            
            await update.message.reply_text(
                f"✅ {BUTTONS[button_id]['name']} uchun APK o'chirildi!"
            )
            logger.info(f"APK o'chirildi: {button_id}")
        except Exception as e:
            logger.error(f"Fayl o'chirishda xatolik: {e}")
            await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    else:
        await update.message.reply_text(
            f"ℹ️ {BUTTONS[button_id]['name']} uchun APK mavjud emas!"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatoliklarni log qilish"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Botni ishga tushirish"""
    try:
        # Application yaratish
        application = Application.builder().token(TOKEN).build()
        
        # Handlerlarni qo'shish
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", admin_help))
        application.add_handler(CommandHandler("list", list_buttons))
        application.add_handler(CommandHandler("upload", upload_apk))
        application.add_handler(CommandHandler("delete", delete_apk))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        # Botni ishga tushirish
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"🤖 Bot ishga tushdi. Admin ID: {ADMIN_ID}")
        
        # Railway uchun webhook yoki polling
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            webhook_url = os.environ.get('RAILWAY_PUBLIC_URL', '')
            if webhook_url:
                application.run_webhook(
                    listen="0.0.0.0",
                    port=port,
                    webhook_url=f"{webhook_url}/webhook"
                )
            else:
                application.run_polling()
        else:
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
