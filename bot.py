import logging
import os
from threading import Thread
from flask import Flask
from telegram.ext import Application
from config import BOT_TOKEN
from database import init_db
from handlers.start import start_handlers
from handlers.order import order_conv_handler
from handlers.track import track_handlers
from handlers.admin import admin_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# خادم Flask للبقاء مستيقظاً
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8000))  # Render يعطي PORT، محلياً 8000
    web_app.run(host='0.0.0.0', port=port)

async def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ حدث خطأ غير متوقع. يرجى المحاولة لاحقًا.",
        )

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة جميع المعالجات
    app.add_handler(order_conv_handler)
    for h in start_handlers:
        app.add_handler(h)
    for h in track_handlers:
        app.add_handler(h)
    for h in admin_handlers:
        app.add_handler(h)
    app.add_error_handler(error_handler)

    # تشغيل Flask في خيط منفصل
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("🌐 خادم Flask يعمل على المنفذ %s", os.environ.get('PORT', 8000))

    logger.info("🚀 البوت يعمل الآن ...")
    app.run_polling()

if __name__ == "__main__":
    main()
