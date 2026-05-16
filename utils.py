import re
import time
from config import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS

user_last_request = {}

def is_valid_whatsapp(number):
    pattern = r"^\+\d{10,15}$"
    return re.match(pattern, number) is not None

def validate_file(file):
    """التحقق من حجم الملف ونوعه"""
    if file.file_size and file.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, "حجم الملف كبير جداً (الحد الأقصى 20 ميجابايت)."
    if file.file_name:
        ext = file.file_name.split('.')[-1].lower() if '.' in file.file_name else ''
        if ext and ext not in ALLOWED_EXTENSIONS:
            return False, f"نوع الملف غير مسموح به. الأنواع المسموحة: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    return True, None

async def flood_control(user_id):
    """التحكم في عدد الطلبات لكل مستخدم (5 طلبات في الدقيقة)"""
    now = time.time()
    if user_id in user_last_request:
        if now - user_last_request[user_id] < 60 / 5:  # 5 طلبات في الدقيقة
            return False
    user_last_request[user_id] = now
    return True