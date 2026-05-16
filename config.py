import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

# إعدادات الحماية
MAX_REQUESTS_PER_MINUTE = 5          # الحد الأقصى للطلبات من المستخدم في الدقيقة
MAX_FILE_SIZE_MB = 20                # الحد الأقصى لحجم الملف المرفوع
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'mp4', 'zip', 'rar'}