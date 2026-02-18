import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables orqali konfiguratsiya
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))  # 0 default qiymat

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID environment variable is not set!")

# APK fayllar uchun papka (Railwayda /app/apk_files ishlatiladi)
APK_FOLDER = "apk_files"
if not os.path.exists(APK_FOLDER):
    os.makedirs(APK_FOLDER)

# Tugmalar ro'yxati va ularning identifikatorlari
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

# Saqlangan APK fayllarni yuklash (agar mavjud bo'lsa)
def load_existing_apks():
    for button_id in BUTTONS.keys():
        file_path = os.path.join(APK_FOLDER, f"{button_id}.apk")
        if os.path.exists(file_path):
            BUTTONS[button_id]["file"] = file_path
            logger.info(f"Loaded APK for {button_id}")

# Botni ishga tushirishda mavjud APKlarni yuklash
load_existing_apks()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi - asosiy menyu"""
    keyboard = []
    
    # Tugmalarni yaratish (faqat APK fayli mavjud bo'lganlar)
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

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugmalar bosilganda ishlaydi"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("get_"):
        button_id = callback_data[4:]  # "get_" dan keyingi qism
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
                    logger.error(f"Error sending file: {e}")
                    await query.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")
            else:
                BUTTONS[button_id]["file"] = None  # Fayl yo'q, yangilaymiz
                await query.message.reply_text("❌ APK fayl topilmadi")

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
            file_size = os.path.getsize(button_info["file"]) / (1024 * 1024)  # MB da
            text += f"✅ {button_info['name']} - {file_size:.2f} MB\n"
        else:
            text += f"❌ {button_info['name']} - APK mavjud emas\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def upload_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """APK fayl yuklash (faqat admin)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu buyruq faqat admin uchun!")
        return
    
    # Buyruqdan keyin tugma nomini olish
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Tugma nomini kiriting!\n"
            "Masalan: /upload betwinner"
        )
        return
    
    button_id = context.args[0].lower()
    
    if button_id not in BUTTONS:
        await update.message.reply_text(
            f"❌ Noto'g'ri tugma nomi!\n"
            f"Mavjud tugmalar: {', '.join(BUTTONS.keys())}"
        )
        return
    
    # Foydalanuvchini APK yuborishga kutish
    context.user_data['waiting_for_apk'] = button_id
    await update.message.reply_text(
        f"📤 {BUTTONS[button_id]['name']} uchun APK faylni yuboring."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yuborilgan hujjatlarni qabul qilish"""
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
    
    # Fayl kengaytmasini tekshirish
    if not document.file_name.endswith('.apk'):
        await update.message.reply_text("❌ Faqat .apk fayllar qabul qilinadi!")
        return
    
    try:
        # Faylni yuklab olish
        file = await context.bot.get_file(document.file_id)
        
        # Faylni saqlash (eski faylni o'chirish)
        file_path = os.path.join(APK_FOLDER, f"{button_id}.apk")
        
        # Eski fayl mavjud bo'lsa o'chirish
        if os.path.exists(file_path):
            os.remove(file_path)
        
        await file.download_to_drive(file_path)
        
        # Tugma ma'lumotlarini yangilash
        BUTTONS[button_id]["file"] = file_path
        
        # Holatni tozalash
        del context.user_data['waiting_for_apk']
        
        await update.message.reply_text(
            f"✅ {BUTTONS[button_id]['name']} uchun APK muvaffaqiyatli yuklandi!"
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
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
            # Faylni o'chirish
            os.remove(BUTTONS[button_id]["file"])
            BUTTONS[button_id]["file"] = None
            
            await update.message.reply_text(
                f"✅ {BUTTONS[button_id]['name']} uchun APK o'chirildi!"
            )
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
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
    logger.info(f"🤖 Bot ishga tushdi on port {port}...")
    
    # Railway uchun webhook yoki polling
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        # Webhook mode for Railway
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
        # Polling mode for local development
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
