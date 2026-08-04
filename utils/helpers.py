import jdatetime

PERSIAN_WEEKDAYS = {
    0: "شنبه", 1: "یکشنبه", 2: "دوشنبه", 3: "سه‌شنبه",
    4: "چهارشنبه", 5: "پنجشنبه", 6: "جمعه",
}

def get_msg_id(msg):
    if not msg: return None
    if isinstance(msg, dict):
        return msg.get("message_id") or msg.get("id")
    return getattr(msg, "message_id", getattr(msg, "id", None))

def get_service_display_name(service_name: str, gender: str = None, short_name: bool = False) -> str:
    if not service_name:
        return "خدمت"
    
    display = service_name
    
    # حذف پسوند دکتر گرایلی از همه‌ی خدمات به جز ویزیت برای جلوگیری از تکرار
    if "دکتر گرایلی" in display and "ویزیت" not in display:
        display = display.replace(" دکتر گرایلی", "").replace("دکتر گرایلی", "").strip()
    
    # اضافه کردن انحصاری نام دکتر در صورت نیاز (فاکتور و متن پیام‌ها)
    if not short_name:
        append_doctor = ["طب سوزنی", "امبدینگ(لاغری)", "اسکن کل بدن", "غمز و رگ گیری"]
        if display in append_doctor:
            display += " دکتر گرایلی"
    
    # برای افزودن جنسیت، نسخه بدون دکتر را مبنا قرار می‌دهیم تا شرط‌ها درست کار کنند
    base_for_gender = display.replace(" دکتر گرایلی", "")
    if gender == "male" and base_for_gender in ["بادکش", "حجامت عام", "زالودرمانی"]:
        display += " آقایان"
    elif gender == "female" and base_for_gender in ["بادکش", "حجامت عام", "زالودرمانی"]:
        display += " بانوان"
        
    return display

def to_jalali_date(date_string: str) -> str:
    try:
        year, month, day = map(int, date_string.split("-"))
        jalali = jdatetime.date.fromgregorian(year=year, month=month, day=day)
        return jalali.strftime("%Y/%m/%d")
    except (ValueError, TypeError):
        return date_string

def to_persian_digits(value: str) -> str:
    translation = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(value).translate(translation)

def to_persian_date(date_string: str) -> str:
    return to_persian_digits(to_jalali_date(date_string))

def to_short_persian_date(date_string: str) -> str:
    try:
        year, month, day = map(int, date_string.split("-"))
        jalali = jdatetime.date.fromgregorian(year=year, month=month, day=day)
        short_year = jalali.year % 100
        result = f"{short_year:02d}/{jalali.month:02d}/{jalali.day:02d}"
        return to_persian_digits(result)
    except (ValueError, TypeError):
        return date_string

def to_date_label(date_string: str) -> str:
    try:
        year, month, day = map(int, date_string.split("-"))
        jalali = jdatetime.date.fromgregorian(year=year, month=month, day=day)
        weekday = PERSIAN_WEEKDAYS[jalali.weekday()]
        return f"{weekday} - {to_short_persian_date(date_string)}"
    except (ValueError, TypeError, KeyError):
        return date_string

async def activate_text_keyboard(bot, chat_id, is_registered=True):
    from utils.keyboards import main_keyboard, register_keyboard
    kb = main_keyboard() if is_registered else register_keyboard()
    await bot.send_message(chat_id, "⌨️ لطفاً مقادیر را تایپ کنید 👇", components=kb)

async def send_welcome_message(target, user_id):
    from database.repository import repository
    from utils.keyboards import main_keyboard, register_keyboard
    
    user = repository.get_user_by_bale_id(user_id)
    patient = repository.get_patient_by_user_id(user["id"]) if user else None

    if patient and patient.get("national_id"):
        text = (
            "🌟 به سامانه نوبت‌دهی درمانگاه طب سنتی دکتر ولی‌الله گرایلی ملک خوش آمدید. 🌟\n\n"
            "برای دریافت نوبت، لطفاً گزینه «دریافت نوبت» را از منوی پایین صفحه انتخاب کنید."
        )
        if hasattr(target, "message") and target.message:
            await target.message.get_bot().send_message(target.message.chat_id, text, components=main_keyboard())
        else:
            await target.reply(text, components=main_keyboard())
    else:
        text = (
            "🌟 به سامانه نوبت‌دهی درمانگاه طب سنتی دکتر ولی‌الله گرایلی ملک خوش آمدید. 🌟\n\n"
            "برای دریافت نوبت، ابتدا باید اطلاعات شما در سامانه ثبت شود.\n\n"
            "لطفاً روی دکمه زیر کلیک کنید 👇"
        )
        if hasattr(target, "message") and target.message:
            await target.message.get_bot().send_message(target.message.chat_id, text, components=register_keyboard())
        else:
            await target.reply(text, components=register_keyboard())