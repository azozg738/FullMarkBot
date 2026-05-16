import os
import sys
from dotenv import load_dotenv

load_dotenv()  # يحمل .env محلياً إن وجد، ولا يضر في Render

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")

if not BOT_TOKEN:
    sys.exit("❌ خطأ: لم يتم العثور على BOT_TOKEN. تأكد من إضافته كمتغير بيئة.")

try:
    CHANNEL_ID = int(CHANNEL_ID)
except (TypeError, ValueError):
    sys.exit("❌ خطأ: CHANNEL_ID غير موجود أو ليس رقماً صحيحاً.")

try:
    ADMIN_IDS = list(map(int, ADMIN_IDS_STR.split(",")))
except:
    sys.exit("❌ خطأ: ADMIN_IDS غير موجود أو صيغته خاطئة. استخدم صيغة: 123,456")

# إعدادات الحماية
MAX_REQUESTS_PER_MINUTE = 5
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'mp4', 'zip', 'rar'}
