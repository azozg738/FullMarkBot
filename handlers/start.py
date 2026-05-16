from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🎯 طلب خدمة جديدة")],
            [KeyboardButton("📋 تتبع حالة الطلب")],
            [KeyboardButton("ℹ️ معلومات عنا / 📞 التواصل")],
        ],
        resize_keyboard=True,
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلًا بك في بوت **FullMark**!\n\n"
        "أكاديمية إتقان التعليمية 🎓🪄\n"
        "اختر أحد الأزرار للبدء:",
        reply_markup=main_keyboard(),
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 **أكاديمية إتقان التعليمية** 🎓🪄\n\n"
        "نقدم خدمات أكاديمية وتقنية وطبية باحترافية عالية.\n"
        "📞 للتواصل: راسلنا على البوت أو عبر الواتساب في طلبك.\n\n"
        "اختر من الأزرار أدناه 👇",
        reply_markup=main_keyboard(),
    )

# قائمة المعالجات الخاصة بهذا الملف
start_handlers = [
    CommandHandler("start", start),
    MessageHandler(filters.Regex("^ℹ️ معلومات عنا / 📞 التواصل$"), about),
]