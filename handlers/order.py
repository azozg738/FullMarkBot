import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters, CommandHandler
)
from database import insert_order
from utils import is_valid_whatsapp, validate_file, flood_control
from config import CHANNEL_ID
from handlers.start import main_keyboard

logger = logging.getLogger(__name__)

# حالات المحادثة
(CHOOSE_SERVICE_TYPE, CHOOSE_SUB_SERVICE, ENTER_NAME, ENTER_WHATSAPP,
 ASK_FILE, RECEIVE_FILE, CONFIRMATION) = range(7)

async def new_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await flood_control(user_id):
        await update.message.reply_text("⚠️ أنت ترسل الطلبات بسرعة كبيرة. انتظر لحظة من فضلك.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("📚 أكاديمية", callback_data="service_أكاديمية")],
        [InlineKeyboardButton("💻 تقنية", callback_data="service_تقنية")],
        [InlineKeyboardButton("🩺 طبية", callback_data="service_طبية")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ]
    await update.message.reply_text(
        "🎯 اختر نوع الخدمة المطلوبة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_SERVICE_TYPE

async def choose_service_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await cancel(update, context)
        return ConversationHandler.END

    service_type = data.replace("service_", "")
    context.user_data["service_type"] = service_type

    if service_type == "أكاديمية":
        subs = [
            ("📝 كتابة بحث", "sub_كتابة بحث"),
            ("📄 إعداد عرض تقديمي", "sub_إعداد عرض تقديمي"),
            ("📖 تلخيص محاضرات", "sub_تلخيص محاضرات"),
            ("🎓 استشارات أكاديمية", "sub_استشارات أكاديمية"),
        ]
    elif service_type == "تقنية":
        subs = [
            ("🖥️ برمجة وتطوير", "sub_برمجة وتطوير"),
            ("🌐 تصميم مواقع", "sub_تصميم مواقع"),
            ("📱 تطبيقات جوال", "sub_تطبيقات جوال"),
            ("🛡️ أمن معلومات", "sub_أمن معلومات"),
        ]
    else:  # طبية
        subs = [
            ("💊 استشارة طبية", "sub_استشارة طبية"),
            ("🩻 تحليل تقارير", "sub_تحليل تقارير"),
            ("🧬 أبحاث طبية", "sub_أبحاث طبية"),
            ("🏥 إدارة صحية", "sub_إدارة صحية"),
        ]

    keyboard = [[InlineKeyboardButton(text, callback_data=cb)] for text, cb in subs]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
    await query.edit_message_text(
        f"📂 اختر الخدمة الفرعية من قسم **{service_type}**:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_SUB_SERVICE

async def choose_sub_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "back_to_main":
        return await new_order_start_edit(query, context)
    if data == "cancel":
        await cancel(update, context)
        return ConversationHandler.END

    sub_service = data.replace("sub_", "")
    context.user_data["sub_service"] = sub_service
    await query.edit_message_text(
        f"✅ اخترت: **{sub_service}**\n\nالآن من فضلك أدخل الاسم الكامل:"
    )
    return ENTER_NAME

async def new_order_start_edit(query, context):
    keyboard = [
        [InlineKeyboardButton("📚 أكاديمية", callback_data="service_أكاديمية")],
        [InlineKeyboardButton("💻 تقنية", callback_data="service_تقنية")],
        [InlineKeyboardButton("🩺 طبية", callback_data="service_طبية")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")],
    ]
    await query.edit_message_text(
        "🎯 اختر نوع الخدمة المطلوبة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_SERVICE_TYPE

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text(
        "📞 أدخل رقم الواتساب (بصيغة دولية، مثال: +966501234567):"
    )
    return ENTER_WHATSAPP

async def enter_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    if not is_valid_whatsapp(number):
        await update.message.reply_text(
            "⚠️ رقم الواتساب غير صحيح. يجب أن يكون بصيغة دولية (مثل +966xxxxxxxxx). حاول مجددًا:"
        )
        return ENTER_WHATSAPP
    context.user_data["whatsapp"] = number
    keyboard = [
        [InlineKeyboardButton("📎 نعم", callback_data="file_yes"),
         InlineKeyboardButton("⏭️ لا", callback_data="file_no")]
    ]
    await update.message.reply_text(
        "📁 هل تريد إرفاق ملف مع الطلب؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ASK_FILE

async def ask_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "file_no":
        context.user_data["file_msg"] = None
        return await show_confirmation(update, context)
    else:
        await query.edit_message_text("📤 أرسل الملف الآن (صورة، مستند، فيديو، أي نوع):")
        return RECEIVE_FILE

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_msg = update.message
    # استخراج الملف للتحقق
    file = None
    if file_msg.document:
        file = file_msg.document
    elif file_msg.photo:
        file = file_msg.photo[-1]
    elif file_msg.video:
        file = file_msg.video

    if file:
        valid, error_msg = validate_file(file)
        if not valid:
            await update.message.reply_text(f"⚠️ {error_msg} أرسل ملفًا آخر أو اختر /cancel للإلغاء.")
            return RECEIVE_FILE

    context.user_data["file_msg"] = file_msg
    return await show_confirmation(update, context)

async def show_confirmation(update, context):
    data = context.user_data
    summary = (
        f"📋 **ملخص الطلب**\n\n"
        f"📂 النوع: {data['service_type']}\n"
        f"📝 الخدمة: {data['sub_service']}\n"
        f"👤 الاسم: {data['full_name']}\n"
        f"📞 واتساب: {data['whatsapp']}\n"
        f"📁 ملف: {'نعم' if data.get('file_msg') else 'لا'}\n\n"
        f"هل تؤكد إرسال الطلب؟"
    )
    keyboard = [
        [InlineKeyboardButton("✅ تأكيد الإرسال", callback_data="confirm_yes"),
         InlineKeyboardButton("❌ إلغاء", callback_data="confirm_no")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_yes":
        await finish_order(update, context)
        return ConversationHandler.END
    else:
        await query.edit_message_text("❌ تم إلغاء الطلب.")
        context.user_data.clear()
        return ConversationHandler.END

async def finish_order(update, context):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    username = user.username or "لا يوجد"
    data = context.user_data

    file_msg = data.get("file_msg")
    file_id = None
    if file_msg:
        if file_msg.document:
            file_id = file_msg.document.file_id
        elif file_msg.photo:
            file_id = file_msg.photo[-1].file_id
        elif file_msg.video:
            file_id = file_msg.video.file_id
        elif file_msg.audio:
            file_id = file_msg.audio.file_id
        elif file_msg.voice:
            file_id = file_msg.voice.file_id

    order_id = insert_order(
        user_id=user_id,
        username=username,
        full_name=data["full_name"],
        whatsapp=data["whatsapp"],
        service_type=data["service_type"],
        sub_service=data["sub_service"],
        file_id=file_id,
    )

    caption = (
        f"🆔 رقم الطلب: #{order_id}\n"
        f"👤 الاسم: {data['full_name']}\n"
        f"📞 واتساب: {data['whatsapp']}\n"
        f"📂 النوع: {data['service_type']}\n"
        f"📝 الخدمة: {data['sub_service']}\n"
        f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"📌 الحالة: جديد"
    )

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
        if file_msg and file_id:
            await context.bot.copy_message(
                chat_id=CHANNEL_ID,
                from_chat_id=file_msg.chat_id,
                message_id=file_msg.message_id,
                caption=caption,
                reply_markup=reply_markup,
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=caption,
                reply_markup=reply_markup,
            )

        await query.edit_message_text(
            f"✅ تم تقديم طلبك بنجاح! رقم طلبك: #{order_id}\nيمكنك تتبع حالته من القائمة الرئيسية."
        )
    except Exception as e:
        logger.error(f"خطأ في إرسال الطلب للقناة: {e}")
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ حدث خطأ أثناء إرسال الطلب، حاول مرة أخرى لاحقاً.",
            reply_markup=main_keyboard(),
        )
    finally:
        context.user_data.clear()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.edit_message_text("❌ تم إلغاء العملية.")
    elif update.message:
        await update.message.reply_text("❌ تم إلغاء العملية.", reply_markup=main_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

order_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^🎯 طلب خدمة جديدة$"), new_order_start)],
    states={
        CHOOSE_SERVICE_TYPE: [CallbackQueryHandler(choose_service_type, pattern="^(service_|cancel)")],
        CHOOSE_SUB_SERVICE: [CallbackQueryHandler(choose_sub_service, pattern="^(sub_|back_to_main|cancel)")],
        ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
        ENTER_WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_whatsapp)],
        ASK_FILE: [CallbackQueryHandler(ask_file, pattern="^file_")],
        RECEIVE_FILE: [MessageHandler(filters.ATTACHMENT, receive_file)],
        CONFIRMATION: [CallbackQueryHandler(confirm_order, pattern="^confirm_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)