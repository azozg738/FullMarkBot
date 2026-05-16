from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database import search_orders
from handlers.start import main_keyboard

async def track_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 أدخل رقم الطلب (مثال: 5) أو الاسم للبحث عن طلبك:")
    context.user_data["awaiting_track"] = True

async def handle_track_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_track"):
        return
    context.user_data["awaiting_track"] = False
    query = update.message.text.strip()
    results = search_orders(query)
    if not results:
        await update.message.reply_text(
            "ℹ️ لم يتم العثور على طلبات تطابق بحثك.",
            reply_markup=main_keyboard(),
        )
        return
    for order in results:
        (
            order_id, user_id, username, full_name, whatsapp,
            service_type, sub_service, status, file_id, created_at
        ) = order
        text = (
            f"🔖 رقم الطلب: #{order_id}\n"
            f"👤 الاسم: {full_name}\n"
            f"📞 واتساب: {whatsapp}\n"
            f"📂 النوع: {service_type}\n"
            f"📝 الخدمة: {sub_service}\n"
            f"📌 الحالة: {status}\n"
            f"📅 تاريخ الطلب: {created_at}"
        )
        await update.message.reply_text(text)
    await update.message.reply_text("اختر من القائمة:", reply_markup=main_keyboard())

track_handlers = [
    MessageHandler(filters.Regex("^📋 تتبع حالة الطلب$"), track_order_start),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_track_input),
]