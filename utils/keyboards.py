from datetime import date
from bale import MenuKeyboardButton, MenuKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from utils.helpers import to_date_label, get_service_display_name

def main_keyboard():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton("📅 دریافت نوبت"), row=1)
    keyboard.add(MenuKeyboardButton("📋 نوبت‌های من"), row=1)
    keyboard.add(MenuKeyboardButton("👤 اطلاعات بیمار"), row=2)
    keyboard.add(MenuKeyboardButton("🏥 اطلاعات درمانگاه"), row=2)
    return keyboard

def register_keyboard():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton("📝 ثبت اطلاعات"), row=1)
    return keyboard

# ==========================================
# کیبوردهای لغو و بازگشت (شیشه‌ای)
# ==========================================

def cancel_only_inline_keyboard(text="❌ لغو ثبت‌نام"):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text, callback_data="register_cancel"), row=1)
    return keyboard

def cancel_back_inline_keyboard(text="❌ لغو ثبت‌نام"):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت به مرحله قبل", callback_data="register_back"), row=1)
    keyboard.add(InlineKeyboardButton(text, callback_data="register_cancel"), row=2)
    return keyboard

def edit_cancel_inline_keyboard(text="❌ لغو ویرایش"):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text, callback_data="patient:edit_cancel"), row=1)
    return keyboard

def edit_back_inline_keyboard(text="❌ لغو ویرایش"):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت به مرحله قبل", callback_data="edit_back"), row=1)
    keyboard.add(InlineKeyboardButton(text, callback_data="patient:edit_cancel"), row=2)
    return keyboard

def other_cancel_inline_keyboard(text=""):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به انتخاب فرد", callback_data="booking_back:target"), row=1)
    return keyboard

def other_back_inline_keyboard(text=""):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت به مرحله قبل", callback_data="other_back"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به انتخاب فرد", callback_data="booking_back:target"), row=2)
    return keyboard

# ==========================================
# کیبوردهای اصلی سیستم
# ==========================================

def patient_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✏️ ویرایش اطلاعات", callback_data="patient:edit"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="booking_back:home"), row=2)
    return keyboard

def gender_keyboard():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton("آقا"), row=1)
    keyboard.add(MenuKeyboardButton("خانم"), row=1)
    return keyboard

def insurance_keyboard():
    keyboard = MenuKeyboardMarkup()
    keyboard.add(MenuKeyboardButton("سلامت"), row=1)
    keyboard.add(MenuKeyboardButton("تأمین اجتماعی"), row=1)
    keyboard.add(MenuKeyboardButton("نیروهای مسلح"), row=2)
    keyboard.add(MenuKeyboardButton("بدون بیمه"), row=2)
    return keyboard

def booking_target_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👤 برای خودم", callback_data="booking_target:self"), row=1)
    keyboard.add(InlineKeyboardButton("👥 برای شخص دیگر", callback_data="booking_target:other"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="booking_back:home"), row=2)
    return keyboard

def clinic_info_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="booking_back:home"), row=1)
    return keyboard

def booking_services_keyboard(services):
    keyboard = InlineKeyboardMarkup()
    services = services or []
    if not services:
        keyboard.add(InlineKeyboardButton("❌ خدمتی وجود ندارد", callback_data="ignore:full"), row=1)
        keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="booking_back:home"), row=2)
        return keyboard

    for index, service in enumerate(services, start=1):
        row = ((index - 1) // 2) + 1
        keyboard.add(InlineKeyboardButton(text=service["name"], callback_data=f"booking_service:{service['id']}"), row=row)

    service_rows = ((len(services) - 1) // 2) + 1
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به انتخاب فرد", callback_data="booking_back:target"), row=service_rows + 1)
    return keyboard

def booking_gender_inline_keyboard(back_to="services"):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👨 آقا", callback_data="booking_gender:male"), row=1)
    keyboard.add(InlineKeyboardButton("👩 خانم", callback_data="booking_gender:female"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت", callback_data=f"booking_back:{back_to}"), row=2)
    return keyboard

def booking_dates_keyboard(dates, service_id=None, gender=None, availability=None):
    keyboard = InlineKeyboardMarkup()
    dates = dates or []
    availability = availability or {}
    row = 1

    for date_string in dates:
        try:
            target_date = date.fromisoformat(str(date_string))
        except (TypeError, ValueError):
            continue
        if target_date.weekday() == 4:
            continue

        status = availability.get(str(date_string), True)
        if isinstance(status, dict): has_available_time = status.get("available", False)
        else: has_available_time = bool(status)

        if has_available_time:
            keyboard.add(InlineKeyboardButton(text=f"📅 {to_date_label(str(date_string))}", callback_data=f"booking_date:{date_string}"), row=row)
        else:
            keyboard.add(InlineKeyboardButton(text=f"❌ {to_date_label(str(date_string))} (تکمیل شده)", callback_data="ignore:full"), row=row)
        row += 1

    keyboard.add(InlineKeyboardButton("↩️ بازگشت به خدمات", callback_data="booking_back:services"), row=row)
    return keyboard

def booking_times_keyboard(times, appointment_date):
    keyboard = InlineKeyboardMarkup()
    valid_times = [item for item in (times or []) if item.get("start_time")]

    if not valid_times:
        keyboard.add(InlineKeyboardButton("❌ ساعتی وجود ندارد", callback_data="ignore:full"), row=1)
        keyboard.add(InlineKeyboardButton("↩️ بازگشت به تاریخ‌ها", callback_data="booking_back:dates"), row=2)
        return keyboard

    for index, item in enumerate(valid_times, start=1):
        start_time = item["start_time"]
        booked_count = int(item.get("booked_count", 0))
        capacity = int(item.get("capacity", 1))
        available = (booked_count < capacity)
        row = ((index - 1) // 2) + 1

        if available:
            keyboard.add(InlineKeyboardButton(text=f"🕐 {start_time}", callback_data=f"booking_time:{appointment_date}:{start_time}"), row=row)
        else:
            keyboard.add(InlineKeyboardButton(text=f"❌ {start_time} (رزرو)", callback_data="ignore:full"), row=row)

    back_row = ((len(valid_times) - 1) // 2) + 2
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به تاریخ‌ها", callback_data="booking_back:dates"), row=back_row)
    return keyboard

def booking_checkout_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ تأیید و ثبت نهایی", callback_data="booking_checkout:confirm"), row=1)
    keyboard.add(InlineKeyboardButton("❌ انصراف", callback_data="booking_checkout:cancel"), row=1)
    return keyboard

def booking_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 نوبت‌های من", callback_data="appointments:menu"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="appointments:home"), row=2)
    return keyboard

def back_to_services_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی خدمات", callback_data="booking_back:services"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="booking_back:home"), row=2)
    return keyboard

def appointments_menu_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 نوبت‌های جاری", callback_data="appointments:current"), row=1)
    keyboard.add(InlineKeyboardButton("📜 تاریخچه نوبت‌ها", callback_data="appointments:history"), row=2)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="appointments:home"), row=3)
    return keyboard

def empty_appointments_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📅 دریافت نوبت", callback_data="booking_start_inline"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="appointments:home"), row=2)
    return keyboard

def appointment_list_keyboard(appointments, prefix):
    keyboard = InlineKeyboardMarkup()
    appointments = appointments or []

    if not appointments:
        keyboard.add(InlineKeyboardButton("❌ نوبتی وجود ندارد", callback_data="ignore:full"), row=1)
        keyboard.add(InlineKeyboardButton("↩️ بازگشت", callback_data="appointments:menu"), row=2)
        return keyboard

    for index, appointment in enumerate(appointments, start=1):
        # با استفاده از short_name=True نام دکتر را در دکمه‌ها حذف می‌کنیم تا متن نصفه نشود
        service_name = get_service_display_name(appointment.get("service_name", ""), appointment.get("gender"), short_name=True)
        appointment_date = appointment.get("appointment_date")
        start_time = appointment.get("start_time", "")

        keyboard.add(InlineKeyboardButton(text=f"{service_name} | {to_date_label(appointment_date)} | {start_time}", callback_data=f"{prefix}:{appointment.get('id')}"), row=index)

    keyboard.add(InlineKeyboardButton("↩️ بازگشت", callback_data="appointments:menu"), row=len(appointments) + 1)
    return keyboard

def appointment_detail_keyboard(appointment_id, can_cancel=True):
    keyboard = InlineKeyboardMarkup()
    row = 1
    if can_cancel:
        keyboard.add(InlineKeyboardButton("❌ لغو نوبت", callback_data=f"appointment_cancel:{appointment_id}"), row=row)
        row += 1
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به نوبت‌ها", callback_data="appointments:current"), row=row)
    return keyboard

def cancel_confirmation_keyboard(appointment_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ بله، لغو کن", callback_data=f"appointment_cancel_confirm:{appointment_id}"), row=1)
    keyboard.add(InlineKeyboardButton("❌ خیر، بازگشت", callback_data=f"appointment_cancel_abort:{appointment_id}"), row=1)
    return keyboard

def cancel_success_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📋 بازگشت به نوبت‌های من", callback_data="appointments:menu"), row=1)
    keyboard.add(InlineKeyboardButton("↩️ بازگشت به منوی اصلی", callback_data="appointments:home"), row=2)
    return keyboard