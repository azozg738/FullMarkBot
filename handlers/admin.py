import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from database import update_order_status, get_order_by_id, get_statistics
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("⛔ غير مصرح لك بتغيير الحالة.", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    if len(parts) != 3:
        return
    order_id = int(parts[1])
    new_status = parts[2]

    # تحديث قاعدة البيانات
    update_order_status(order_id, new_status)

    # إشعار المستخدم صاحب الطلب
    order = get_order_by_id(order_id)
    if order:
        user_id = order[1]  # user_id في الفهرس 1
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🔔 حالة طلبك #{order_id} تغيرت إلى: **{new_status}**"
            )
        except Exception as e:
            logger.warning(f"تعذر إرسال إشعار للمستخدم {user_id}: {e}")

    # تحديث الرسالة في القناة
    old_caption = query.message.caption or ""
    old_text = query.message.text or ""
    if old_caption:
        old_content = old_caption
        is_media = True
    else:
        old_content = old_text
        is_media = False

    lines = old_content.split("\n")
    new_lines = []
    for line in lines:
        if line.startswith("📌 الحالة:"):
            new_lines.append(f"📌 الحالة: {new_status}")
        else:
            new_lines.append(line)
    updated_content = "\n".join(new_lines)

    keyboard = [
        [
            InlineKeyboardButton("✅ مقبول", callback_data=f"status_{order_id}_مقبول"),
            InlineKeyboardButton("❌ مرفوض", callback_data=f"status_{order_id}_مرفوض"),
            InlineKeyboardButton("🔄 قيد العمل", callback_data=f"status_{order_id}_قيد العمل"),
            InlineKeyboardButton("🎉 تم الانجاز", callback_data=f"status_{order_id}_تم الانجاز"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if is_media:
            await query.edit_message_caption(caption=updated_content, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=updated_content, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"فشل تحديث الرسالة في القناة: {e}")
        await query.answer("⚠️ حدث خطأ أثناء تحديث الحالة.", show_alert=True)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح لك.")
        return

    total, statuses = get_statistics()
    stats_text = f"📊 **إحصائيات البوت**\n\nمجموع الطلبات: {total}\n"
    for status, count in statuses:
        stats_text += f"- {status}: {count}\n"
    await update.message.reply_text(stats_text)

admin_handlers = [
    CallbackQueryHandler(status_callback, pattern="^status_"),
    CommandHandler("admin", admin_stats),
]