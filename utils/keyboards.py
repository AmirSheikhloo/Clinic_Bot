from datetime import date

from bale import (
    MenuKeyboardButton,
    MenuKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from utils.helpers import to_date_label


# =========================================================
# Main Keyboard
# =========================================================

def main_keyboard():
    """
    منوی اصلی ربات

    گزینه‌ها:
    - دریافت نوبت
    - نوبت‌های من
    - اطلاعات بیمار
    - اطلاعات درمانگاه
    """

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton("📅 دریافت نوبت"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("📋 نوبت‌های من"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("👤 اطلاعات بیمار"),
        row=2,
    )

    keyboard.add(
        MenuKeyboardButton("🏥 اطلاعات درمانگاه"),
        row=2,
    )

    return keyboard


# =========================================================
# Patient Keyboard
# =========================================================

def patient_keyboard():
    """
    منوی اطلاعات بیمار
    """

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton("✏️ ویرایش اطلاعات بیمار"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("🏠 بازگشت به خانه"),
        row=2,
    )

    return keyboard


# =========================================================
# Gender Keyboard
# =========================================================

def gender_keyboard():
    """
    کیبورد جنسیت برای ثبت/ویرایش اطلاعات بیمار
    """

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton("آقا"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("خانم"),
        row=1,
    )

    return keyboard


# =========================================================
# Insurance Keyboard
# =========================================================

def insurance_keyboard():
    """
    کیبورد نوع بیمه
    """

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton("سلامت"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("تأمین اجتماعی"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("نیروهای مسلح"),
        row=2,
    )

    keyboard.add(
        MenuKeyboardButton("بدون بیمه"),
        row=2,
    )

    return keyboard


# =========================================================
# Booking Target
# =========================================================

def booking_target_keyboard():
    """
    اولین مرحله دریافت نوبت:

    نوبت برای:
    - خودم
    - شخص دیگر
    """

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "👤 برای خودم",
            callback_data="booking_target:self",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "👥 برای شخص دیگر",
            callback_data="booking_target:other",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به منوی اصلی",
            callback_data="booking_back:home",
        ),
        row=2,
    )

    return keyboard


# =========================================================
# Booking Services
# =========================================================

def booking_services_keyboard(services):
    """
    نمایش خدمات قابل دریافت نوبت
    """

    keyboard = InlineKeyboardMarkup()

    services = services or []

    if not services:
        keyboard.add(
            InlineKeyboardButton(
                "❌ خدمتی وجود ندارد",
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                "↩️ بازگشت به انتخاب فرد",
                callback_data="booking_back:target",
            ),
            row=2,
        )

        return keyboard

    for index, service in enumerate(
        services,
        start=1,
    ):
        row = ((index - 1) // 2) + 1

        keyboard.add(
            InlineKeyboardButton(
                text=service["name"],
                callback_data=(
                    f"booking_service:{service['id']}"
                ),
            ),
            row=row,
        )

    service_rows = (
        ((len(services) - 1) // 2) + 1
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به انتخاب فرد",
            callback_data="booking_back:target",
        ),
        row=service_rows + 1,
    )

    return keyboard


# =========================================================
# Booking Gender
# =========================================================

def booking_gender_keyboard(back_to="services"):
    """
    انتخاب جنسیت برای خدماتی که به جنسیت وابسته هستند.
    """

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "👨 آقا",
            callback_data="booking_gender:male",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "👩 خانم",
            callback_data="booking_gender:female",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data=f"booking_back:{back_to}",
        ),
        row=2,
    )

    return keyboard


# =========================================================
# Booking Dates
# =========================================================

def booking_dates_keyboard(
    dates,
    service_id=None,
    gender=None,
    availability=None,
):
    """
    نمایش تاریخ‌های قابل رزرو.

    نکات:
    - جمعه‌ها اصلاً نمایش داده نمی‌شوند.
    - تاریخ تکمیل‌شده با «❌ ... - تکمیل شده» نمایش داده می‌شود.
    - تاریخ تکمیل‌شده callback ندارد و قابل انتخاب نیست.
    - وضعیت تکمیل بودن باید توسط handler/service محاسبه و
      در availability به این تابع داده شود.

    availability می‌تواند به یکی از این شکل‌ها باشد:

        {
            "2026-08-02": True,
            "2026-08-03": False,
        }

    True  = دارای حداقل یک ساعت آزاد
    False = کاملاً تکمیل شده

    یا:

        {
            "2026-08-02": {
                "available": True,
            },
            "2026-08-03": {
                "available": False,
            },
        }
    """

    keyboard = InlineKeyboardMarkup()

    dates = dates or []
    availability = availability or {}

    row = 1

    for date_string in dates:

        try:
            target_date = date.fromisoformat(
                str(date_string)
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        # =================================================
        # Friday = Clinic Holiday
        # =================================================

        if target_date.weekday() == 4:
            continue

        # =================================================
        # Determine availability
        # =================================================

        status = availability.get(
            str(date_string)
        )

        if isinstance(status, dict):
            has_available_time = bool(
                status.get("available", False)
            )

        elif isinstance(status, bool):
            has_available_time = status

        elif status is None:
            # اگر handler وضعیت را نفرستاده،
            # تاریخ را قابل انتخاب در نظر می‌گیریم.
            #
            # بررسی واقعی ظرفیت باید در handler/service انجام شود.
            has_available_time = True

        else:
            has_available_time = bool(status)

        # =================================================
        # Available Date
        # =================================================

        if has_available_time:

            button = InlineKeyboardButton(
                text=(
                    f"📅 "
                    f"{to_date_label(str(date_string))}"
                ),
                callback_data=(
                    f"booking_date:{date_string}"
                ),
            )

        # =================================================
        # Full Date
        # =================================================

        else:

            button = InlineKeyboardButton(
                text=(
                    f"❌ "
                    f"{to_date_label(str(date_string))}"
                    f" - تکمیل شده"
                ),
            )

        keyboard.add(
            button,
            row=row,
        )

        row += 1

    # =====================================================
    # Back
    # =====================================================

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به انتخاب خدمت",
            callback_data="booking_back:services",
        ),
        row=row,
    )

    return keyboard


# =========================================================
# Booking Times
# =========================================================

def booking_times_keyboard(
    times,
    appointment_date,
):
    """
    نمایش ساعت‌های نوبت.

    times باید از schedule_service دریافت شده باشد.

    ساختار مورد انتظار:

        [
            {
                "start_time": "08:00",
                "booked_count": 0,
                "capacity": 1,
            },
            ...
        ]

    ساعت آزاد:
        callback_data دارد.

    ساعت تکمیل:
        callback_data ندارد.
    """

    keyboard = InlineKeyboardMarkup()

    valid_times = [
        item
        for item in (times or [])
        if item.get("start_time")
    ]

    # =====================================================
    # No Times
    # =====================================================

    if not valid_times:

        keyboard.add(
            InlineKeyboardButton(
                "❌ ساعتی برای این تاریخ وجود ندارد",
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                "↩️ بازگشت به انتخاب تاریخ",
                callback_data="booking_back:dates",
            ),
            row=2,
        )

        return keyboard

    # =====================================================
    # Time Buttons
    # =====================================================

    for index, item in enumerate(
        valid_times,
        start=1,
    ):

        start_time = item["start_time"]

        booked_count = int(
            item.get(
                "booked_count",
                0,
            )
        )

        capacity = int(
            item.get(
                "capacity",
                1,
            )
        )

        available = (
            booked_count < capacity
        )

        row = ((index - 1) // 2) + 1

        # =================================================
        # Available
        # =================================================

        if available:

            button = InlineKeyboardButton(
                text=f"🕐 {start_time}",
                callback_data=(
                    f"booking_time:"
                    f"{appointment_date}:"
                    f"{start_time}"
                ),
            )

        # =================================================
        # Full
        # =================================================

        else:

            button = InlineKeyboardButton(
                text=(
                    f"❌ {start_time}"
                    f" - تکمیل شده"
                ),
            )

        keyboard.add(
            button,
            row=row,
        )

    # =====================================================
    # Back
    # =====================================================

    back_row = (
        ((len(valid_times) - 1) // 2) + 2
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به انتخاب تاریخ",
            callback_data="booking_back:dates",
        ),
        row=back_row,
    )

    return keyboard


# =========================================================
# Booking Confirmation
# =========================================================

def booking_confirmation_keyboard():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "📋 نوبت‌های من",
            callback_data="appointments:menu",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data="appointments:home",
        ),
        row=1,
    )

    return keyboard


# =========================================================
# Appointments Menu
# =========================================================

def appointments_menu_keyboard():

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "📋 نوبت‌های جاری",
            callback_data="appointments:current",
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "📜 تاریخچه نوبت‌ها",
            callback_data="appointments:history",
        ),
        row=2,
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به منوی اصلی",
            callback_data="appointments:home",
        ),
        row=3,
    )

    return keyboard


# =========================================================
# Appointment List
# =========================================================

def appointment_list_keyboard(
    appointments,
    prefix,
):
    """
    لیست نوبت‌ها.
    """

    keyboard = InlineKeyboardMarkup()

    appointments = appointments or []

    if not appointments:

        keyboard.add(
            InlineKeyboardButton(
                "❌ نوبتی وجود ندارد",
            ),
            row=1,
        )

        keyboard.add(
            InlineKeyboardButton(
                "↩️ بازگشت",
                callback_data="appointments:menu",
            ),
            row=2,
        )

        return keyboard

    for index, appointment in enumerate(
        appointments,
        start=1,
    ):

        service_name = appointment.get(
            "service_name",
            "خدمت",
        )

        appointment_date = appointment.get(
            "appointment_date"
        )

        start_time = appointment.get(
            "start_time",
            "",
        )

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"{service_name}"
                    f" | "
                    f"{to_date_label(appointment_date)}"
                    f" | "
                    f"{start_time}"
                ),
                callback_data=(
                    f"{prefix}:"
                    f"{appointment.get('id')}"
                ),
            ),
            row=index,
        )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data="appointments:menu",
        ),
        row=len(appointments) + 1,
    )

    return keyboard


# =========================================================
# Appointment Detail
# =========================================================

def appointment_detail_keyboard(
    appointment_id,
    can_cancel=True,
):
    """
    جزئیات نوبت.
    """

    keyboard = InlineKeyboardMarkup()

    row = 1

    if can_cancel:

        keyboard.add(
            InlineKeyboardButton(
                "❌ لغو نوبت",
                callback_data=(
                    f"appointment_cancel:"
                    f"{appointment_id}"
                ),
            ),
            row=row,
        )

        row += 1

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به نوبت‌ها",
            callback_data="appointments:current",
        ),
        row=row,
    )

    return keyboard


# =========================================================
# Cancel Confirmation
# =========================================================

def cancel_confirmation_keyboard(
    appointment_id,
):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "✅ بله، لغو کن",
            callback_data=(
                f"appointment_cancel_confirm:"
                f"{appointment_id}"
            ),
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت",
            callback_data=(
                f"appointment_cancel_abort:"
                f"{appointment_id}"
            ),
        ),
        row=2,
    )

    return keyboard


# =========================================================
# Cancel Success
# =========================================================

def cancel_success_home_keyboard():

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton(
            "🏠 بازگشت به خانه"
        ),
        row=1,
    )

    return keyboard


# =========================================================
# Profiles
# =========================================================

def profiles_keyboard(
    profiles,
):
    """
    لیست پروفایل‌های بیمار برای رزرو
    برای شخص دیگر.
    """

    keyboard = InlineKeyboardMarkup()

    profiles = profiles or []

    for index, profile in enumerate(
        profiles,
        start=1,
    ):

        first_name = profile.get(
            "first_name",
            "",
        )

        last_name = profile.get(
            "last_name",
            "",
        )

        keyboard.add(
            InlineKeyboardButton(
                text=(
                    f"{first_name} "
                    f"{last_name}"
                ).strip(),
                callback_data=(
                    f"profile_select:"
                    f"{profile.get('id')}"
                ),
            ),
            row=index,
        )

    keyboard.add(
        InlineKeyboardButton(
            "➕ ثبت فرد جدید",
            callback_data="profile_add",
        ),
        row=len(profiles) + 1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به انتخاب فرد",
            callback_data="profile_home",
        ),
        row=len(profiles) + 2,
    )

    return keyboard


# =========================================================
# Profile Enter
# =========================================================

def profile_enter_keyboard(
    patient_id,
):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "👤 ورود به این پروفایل",
            callback_data=(
                f"profile_enter:"
                f"{patient_id}"
            ),
        ),
        row=1,
    )

    keyboard.add(
        InlineKeyboardButton(
            "↩️ بازگشت به فهرست افراد",
            callback_data="profile_list",
        ),
        row=2,
    )

    return keyboard