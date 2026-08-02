from datetime import datetime, timedelta

from bale import (
    Message,
    CallbackQuery,
)

from database.repository import repository

from services.schedule_service import (
    schedule_service,
)

from utils.helpers import (
    to_persian_date,
)

from utils.keyboards import (
    booking_target_keyboard,
    booking_services_keyboard,
    booking_gender_keyboard,
    booking_dates_keyboard,
    booking_times_keyboard,
    booking_confirmation_keyboard,
    gender_keyboard,
    insurance_keyboard,
    main_keyboard,
)

from utils.state_manager import (
    state_manager,
)

from utils.validators import (
    validate_full_name,
    validate_national_id,
    validate_phone_number,
)


# =========================================================
# States
# =========================================================

BOOKING_TARGET = "booking_target"
BOOKING_SERVICE = "booking_service"
BOOKING_GENDER = "booking_gender"
BOOKING_DATE = "booking_date"
BOOKING_TIME = "booking_time"

OTHER_PATIENT_NAME = "booking_other_name"
OTHER_PATIENT_NATIONAL_ID = "booking_other_national_id"
OTHER_PATIENT_PHONE = "booking_other_phone"
OTHER_PATIENT_GENDER = "booking_other_gender"
OTHER_PATIENT_INSURANCE = "booking_other_insurance"


# =========================================================
# Services
# =========================================================

SERVICE_DEFINITIONS = {
    "ویزیت دکتر": False,
    "بادکش": True,
    "حجامت": True,
    "فصد": True,
    "زالودرمانی": True,
}


GENDER_MAP = {
    "آقا": "male",
    "خانم": "female",
}


INSURANCE_MAP = {
    "سلامت": "health",
    "تأمین اجتماعی": "social_security",
    "نیروهای مسلح": "armed_forces",
    "بدون بیمه": "none",
}


# =========================================================
# Helpers
# =========================================================

def get_selected_patient(
    user_id: int,
):

    selected_id = (
        state_manager.get_context(
            user_id,
            "selected_patient_id",
        )
    )

    user = (
        repository.get_user_by_bale_id(
            user_id
        )
    )

    if user is None:
        return None, None

    profiles = (
        repository.get_patient_profiles(
            user["id"]
        )
    )

    if not profiles:
        return user, None

    if selected_id is not None:

        patient = next(
            (
                item
                for item in profiles
                if item["id"]
                == selected_id
            ),
            None,
        )

        if patient is not None:
            return user, patient

    patient = next(
        (
            item
            for item in profiles
            if item.get("user_id")
            == user["id"]
        ),
        profiles[0],
    )

    state_manager.set_context(
        user_id,
        "selected_patient_id",
        patient["id"],
    )

    return user, patient


def get_service_record(
    service_id: int,
):

    try:
        service_id = int(
            service_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    services = (
        repository.get_services()
    )

    for service in services:

        if int(
            service["id"]
        ) == service_id:

            return service

    return None


def get_services_for_booking():

    services = (
        repository.get_services()
    )

    wanted = set(
        SERVICE_DEFINITIONS.keys()
    )

    result = [
        service
        for service in services
        if service.get("name")
        in wanted
    ]

    order = {
        name: index
        for index, name
        in enumerate(
            SERVICE_DEFINITIONS.keys()
        )
    }

    result.sort(
        key=lambda item:
        order.get(
            item.get("name"),
            999,
        )
    )

    return result


def service_requires_gender(
    service_name: str,
) -> bool:

    return bool(
        SERVICE_DEFINITIONS.get(
            service_name,
            False,
        )
    )


def get_appointment_duration():

    value = (
        repository.get_setting(
            "appointment_duration"
        )
    )

    try:

        return int(
            value or "30"
        )

    except (
        TypeError,
        ValueError,
    ):

        return 30


async def delete_callback_message(
    query: CallbackQuery,
):

    if not query.message:
        return

    try:

        await query.message.delete()

    except Exception:

        pass


async def send_callback_message(
    query: CallbackQuery,
    text: str,
    components=None,
    delete_message=True,
):

    if not query.message:
        return

    bot = query.message.get_bot()
    chat_id = query.message.chat_id

    if delete_message:

        await delete_callback_message(
            query
        )

    await bot.send_message(
        chat_id,
        text,
        components=components,
    )


# =========================================================
# Show Services
# =========================================================

async def show_services(
    target,
    user_id: int,
):

    services = (
        get_services_for_booking()
    )

    if not services:

        text = (
            "در حال حاضر خدمات "
            "نوبت‌دهی در سیستم ثبت نشده است."
        )

        if isinstance(
            target,
            CallbackQuery,
        ):

            await send_callback_message(
                target,
                text,
                components=main_keyboard(),
            )

        else:

            await target.reply(
                text,
                components=main_keyboard(),
            )

        return

    state_manager.set_state(
        user_id,
        BOOKING_SERVICE,
    )

    state_manager.set_data(
        user_id,
        "services",
        services,
    )

    text = (
        "📅 دریافت نوبت\n\n"
        "لطفاً خدمت مورد نظر خود را انتخاب کنید:"
    )

    keyboard = (
        booking_services_keyboard(
            services
        )
    )

    if isinstance(
        target,
        CallbackQuery,
    ):

        await send_callback_message(
            target,
            text,
            components=keyboard,
        )

    else:

        await target.reply(
            text,
            components=keyboard,
        )


# =========================================================
# Booking Start
# =========================================================

async def handle_booking_start(
    message: Message,
):

    user_id = message.author.id

    user = (
        repository.get_user_by_bale_id(
            user_id
        )
    )

    if user is None:

        await message.reply(
            "اطلاعات کاربری شما پیدا نشد.\n"
            "لطفاً ابتدا /start را بزنید."
        )

        return

    state_manager.clear_state(
        user_id
    )

    state_manager.set_state(
        user_id,
        BOOKING_TARGET,
    )

    await message.reply(
        "📅 دریافت نوبت\n\n"
        "لطفاً مشخص کنید نوبت را برای چه کسی می‌خواهید:",
        components=booking_target_keyboard(),
    )


# =========================================================
# Target
# =========================================================

async def handle_booking_target_callback(
    query: CallbackQuery,
):

    user_id = query.user.id
    data = query.data or ""

    if not data.startswith(
        "booking_target:"
    ):
        return

    if (
        state_manager.get_state(
            user_id
        )
        != BOOKING_TARGET
    ):
        return

    target = data.split(
        ":",
        1,
    )[1]

    # -----------------------------------------------------
    # Self
    # -----------------------------------------------------

    if target == "self":

        user, patient = (
            get_selected_patient(
                user_id
            )
        )

        if (
            user is None
            or patient is None
        ):

            await send_callback_message(
                query,
                (
                    "برای دریافت نوبت برای "
                    "خودتان، ابتدا اطلاعات "
                    "بیمار را ثبت کنید."
                ),
                components=main_keyboard(),
            )

            return

        state_manager.set_data(
            user_id,
            "booking_target",
            "self",
        )

        state_manager.set_data(
            user_id,
            "booking_patient_id",
            patient["id"],
        )

        await show_services(
            query,
            user_id,
        )

        return

    # -----------------------------------------------------
    # Other Person
    # -----------------------------------------------------

    if target == "other":

        state_manager.clear_state(
            user_id
        )

        state_manager.set_data(
            user_id,
            "booking_target",
            "other",
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_NAME,
        )

        await send_callback_message(
            query,
            (
                "👥 ثبت اطلاعات فرد دیگر\n\n"
                "لطفاً نام و نام خانوادگی "
                "فرد موردنظر را وارد کنید:\n\n"
                "مثال: علی رضایی"
            ),
        )


# =========================================================
# Service
# =========================================================

async def handle_booking_service_callback(
    query: CallbackQuery,
):

    user_id = query.user.id
    data = query.data or ""

    if not data.startswith(
        "booking_service:"
    ):
        return

    if (
        state_manager.get_state(
            user_id
        )
        != BOOKING_SERVICE
    ):
        return

    try:

        service_id = int(
            data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        return

    service = get_service_record(
        service_id
    )

    if (
        service is None
        or service["name"]
        not in SERVICE_DEFINITIONS
    ):

        await send_callback_message(
            query,
            "خدمت انتخاب‌شده معتبر نیست.",
            components=booking_services_keyboard(
                get_services_for_booking()
            ),
        )

        return

    state_manager.set_data(
        user_id,
        "service_id",
        service_id,
    )

    state_manager.set_data(
        user_id,
        "service_name",
        service["name"],
    )

    target = (
        state_manager.get_data(
            user_id,
            "booking_target",
        )
    )

    # -----------------------------------------------------
    # Service requires gender
    # -----------------------------------------------------

    if service_requires_gender(
        service["name"]
    ):

        state_manager.set_state(
            user_id,
            BOOKING_GENDER,
        )

        if target == "other":

            gender_text = (
                "لطفاً جنسیت بیمار را انتخاب کنید:"
            )

        else:

            gender_text = (
                "لطفاً جنسیت خود را انتخاب کنید:"
            )

        await send_callback_message(
            query,
            (
                f"🏥 خدمت انتخاب‌شده: "
                f"{service['name']}\n\n"
                f"{gender_text}"
            ),
            components=booking_gender_keyboard(
                back_to="services"
            ),
        )

        return

    # -----------------------------------------------------
    # Doctor Visit
    # -----------------------------------------------------

    if target == "other":

        gender = state_manager.get_data(
            user_id,
            "other_gender",
        )

    else:

        _, patient = (
            get_selected_patient(
                user_id
            )
        )

        gender = (
            patient.get("gender")
            if patient
            else None
        )

    if gender not in (
        "male",
        "female",
    ):

        await send_callback_message(
            query,
            (
                "جنسیت بیمار ثبت نشده است.\n"
                "لطفاً ابتدا اطلاعات بیمار "
                "را تکمیل کنید."
            ),
            components=main_keyboard(),
        )

        state_manager.clear_state(
            user_id
        )

        return

    state_manager.set_data(
        user_id,
        "gender",
        gender,
    )

    await show_booking_dates(
        query,
        user_id,
    )


# =========================================================
# Gender
# =========================================================

async def handle_booking_gender_callback(
    query: CallbackQuery,
):

    user_id = query.user.id
    data = query.data or ""

    if not data.startswith(
        "booking_gender:"
    ):
        return

    if (
        state_manager.get_state(
            user_id
        )
        != BOOKING_GENDER
    ):
        return

    gender = data.split(
        ":",
        1,
    )[1]

    if gender not in (
        "male",
        "female",
    ):
        return

    state_manager.set_data(
        user_id,
        "gender",
        gender,
    )

    if (
        state_manager.get_data(
            user_id,
            "booking_target",
        )
        == "other"
    ):

        state_manager.set_data(
            user_id,
            "other_gender",
            gender,
        )

    await show_booking_dates(
        query,
        user_id,
    )


# =========================================================
# Dates
# =========================================================

async def show_booking_dates(
    query: CallbackQuery,
    user_id: int,
):

    service_id = (
        state_manager.get_data(
            user_id,
            "service_id",
        )
    )

    gender = (
        state_manager.get_data(
            user_id,
            "gender",
        )
    )

    service_name = (
        state_manager.get_data(
            user_id,
            "service_name",
            "خدمت",
        )
    )

    if (
        service_id is None
        or gender not in (
            "male",
            "female",
            "all",
        )
    ):

        await send_callback_message(
            query,
            (
                "اطلاعات رزرو ناقص است.\n"
                "لطفاً دوباره دریافت نوبت "
                "را شروع کنید."
            ),
            components=main_keyboard(),
        )

        state_manager.clear_state(
            user_id
        )

        return

    dates = (
        schedule_service.get_available_dates(
            service_id=service_id,
            gender=gender,
            days_ahead=7,
        )
    )

    state_manager.set_data(
        user_id,
        "dates",
        dates,
    )

    state_manager.set_state(
        user_id,
        BOOKING_DATE,
    )

    await send_callback_message(
        query,
        (
            f"🏥 خدمت: {service_name}\n\n"
            "لطفاً تاریخ موردنظر را انتخاب کنید:\n\n"
            "❌ تاریخ‌های تکمیل‌شده "
            "قابل انتخاب نیستند."
        ),
        components=booking_dates_keyboard(
            dates,
            service_id=service_id,
            gender=gender,
        ),
    )


# =========================================================
# Date Callback
# =========================================================

async def handle_booking_date_callback(
    query: CallbackQuery,
):

    user_id = query.user.id
    data = query.data or ""

    if not data.startswith(
        "booking_date:"
    ):
        return

    if (
        state_manager.get_state(
            user_id
        )
        != BOOKING_DATE
    ):
        return

    appointment_date = data.split(
        ":",
        1,
    )[1]

    dates = (
        state_manager.get_data(
            user_id,
            "dates",
            [],
        )
    )

    if (
        appointment_date not in dates
        or schedule_service.is_friday(
            appointment_date
        )
    ):
        return

    service_id = (
        state_manager.get_data(
            user_id,
            "service_id",
        )
    )

    gender = (
        state_manager.get_data(
            user_id,
            "gender",
        )
    )

    if (
        service_id is None
        or gender not in (
            "male",
            "female",
            "all",
        )
    ):
        return

    times = (
        schedule_service.get_available_times(
            service_id=service_id,
            appointment_date=appointment_date,
            gender=gender,
        )
    )

    has_available_time = any(
        int(
            item.get(
                "booked_count",
                0,
            )
            or 0
        )
        <
        int(
            item.get(
                "capacity",
                1,
            )
            or 1
        )
        for item in times
    )

    if not has_available_time:

        await show_booking_dates(
            query,
            user_id,
        )

        return

    state_manager.set_data(
        user_id,
        "appointment_date",
        appointment_date,
    )

    state_manager.set_data(
        user_id,
        "times",
        times,
    )

    state_manager.set_state(
        user_id,
        BOOKING_TIME,
    )

    service_name = (
        state_manager.get_data(
            user_id,
            "service_name",
            "خدمت",
        )
    )

    await send_callback_message(
        query,
        (
            f"🏥 خدمت: {service_name}\n"
            f"📅 تاریخ: "
            f"{to_persian_date(appointment_date)}\n\n"
            "لطفاً ساعت موردنظر را انتخاب کنید:"
        ),
        components=booking_times_keyboard(
            times,
            appointment_date,
        ),
    )


# =========================================================
# Time Callback
# =========================================================

async def handle_booking_time_callback(
    query: CallbackQuery,
):

    user_id = query.user.id
    data = query.data or ""

    if not data.startswith(
        "booking_time:"
    ):
        return

    if (
        state_manager.get_state(
            user_id
        )
        != BOOKING_TIME
    ):
        return

    parts = data.split(
        ":",
        2,
    )

    if len(parts) != 3:
        return

    appointment_date = parts[1]
    start_time = parts[2]

    service_id = (
        state_manager.get_data(
            user_id,
            "service_id",
        )
    )

    gender = (
        state_manager.get_data(
            user_id,
            "gender",
        )
    )

    if (
        service_id is None
        or gender not in (
            "male",
            "female",
            "all",
        )
    ):
        return

    # ظرفیت را درست در لحظه ثبت دوباره چک می‌کنیم.

    if not schedule_service.is_slot_available(
        service_id=service_id,
        appointment_date=appointment_date,
        start_time=start_time,
        gender=gender,
    ):

        times = (
            schedule_service.get_available_times(
                service_id=service_id,
                appointment_date=appointment_date,
                gender=gender,
            )
        )

        await send_callback_message(
            query,
            (
                "⚠️ این ساعت همین الان "
                "دیگر قابل رزرو نیست.\n\n"
                "لطفاً ساعت دیگری انتخاب کنید."
            ),
            components=booking_times_keyboard(
                times,
                appointment_date,
            ),
        )

        return

    user, patient = (
        get_selected_patient(
            user_id
        )
    )

    target = (
        state_manager.get_data(
            user_id,
            "booking_target",
        )
    )

    if target == "other":

        patient_id = (
            state_manager.get_data(
                user_id,
                "booking_patient_id",
            )
        )

    else:

        if (
            user is None
            or patient is None
        ):
            return

        patient_id = patient["id"]

    if patient_id is None:

        await send_callback_message(
            query,
            (
                "اطلاعات بیمار پیدا نشد.\n"
                "لطفاً دوباره فرآیند را شروع کنید."
            ),
            components=main_keyboard(),
        )

        state_manager.clear_state(
            user_id
        )

        return

    duration = (
        get_appointment_duration()
    )

    try:

        start = datetime.strptime(
            start_time,
            "%H:%M",
        )

        end_time = (
            start
            + timedelta(
                minutes=duration
            )
        ).strftime(
            "%H:%M"
        )

    except ValueError:

        return

    # برای appointment مقدار واقعی gender
    # باید male/female باشد.

    appointment_gender = gender

    if gender == "all":

        appointment_gender = (
            patient.get("gender")
            if patient
            else "male"
        )

    try:

        appointment_id = (
            repository.create_appointment_if_available(
                patient_id=patient_id,
                service_id=service_id,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                gender=appointment_gender,
                status="scheduled",
                created_by=(
                    user["id"]
                    if user
                    else None
                ),
            )
        )

    except Exception:

        await send_callback_message(
            query,
            (
                "❌ هنگام ثبت نوبت مشکلی "
                "پیش آمد.\n"
                "لطفاً دوباره تلاش کنید."
            ),
            components=main_keyboard(),
        )

        state_manager.clear_state(
            user_id
        )

        return

    if appointment_id is None:

        times = (
            schedule_service.get_available_times(
                service_id=service_id,
                appointment_date=appointment_date,
                gender=gender,
            )
        )

        await send_callback_message(
            query,
            (
                "⚠️ این ساعت دیگر قابل رزرو نیست.\n"
                "لطفاً ساعت دیگری انتخاب کنید."
            ),
            components=booking_times_keyboard(
                times,
                appointment_date,
            ),
        )

        return

    service_name = (
        state_manager.get_data(
            user_id,
            "service_name",
            "خدمت",
        )
    )

    state_manager.clear_state(
        user_id
    )

    await send_callback_message(
        query,
        (
            "✅ نوبت شما با موفقیت ثبت شد.\n\n"
            f"🏥 خدمت: {service_name}\n"
            f"📅 تاریخ: "
            f"{to_persian_date(appointment_date)}\n"
            f"🕐 ساعت: "
            f"{start_time} تا {end_time}\n"
            f"🔖 کد پیگیری: "
            f"CF-{appointment_id:06d}"
        ),
        components=booking_confirmation_keyboard(),
    )


# =========================================================
# Back
# =========================================================

async def handle_booking_back_callback(
    query: CallbackQuery,
):

    user_id = query.user.id
    data = query.data or ""

    if not data.startswith(
        "booking_back:"
    ):
        return

    destination = data.split(
        ":",
        1,
    )[1]

    # -----------------------------------------------------
    # Home
    # -----------------------------------------------------

    if destination == "home":

        state_manager.clear_state(
            user_id
        )

        await send_callback_message(
            query,
            "به منوی اصلی بازگشتید.",
            components=main_keyboard(),
        )

        return

    # -----------------------------------------------------
    # Target
    # -----------------------------------------------------

    if destination == "target":

        state_manager.clear_state(
            user_id
        )

        state_manager.set_state(
            user_id,
            BOOKING_TARGET,
        )

        await send_callback_message(
            query,
            (
                "📅 دریافت نوبت\n\n"
                "لطفاً مشخص کنید نوبت را "
                "برای چه کسی می‌خواهید:"
            ),
            components=booking_target_keyboard(),
        )

        return

    # -----------------------------------------------------
    # Services
    # -----------------------------------------------------

    if destination == "services":

        await show_services(
            query,
            user_id,
        )

        return

    # -----------------------------------------------------
    # Dates
    # -----------------------------------------------------

    if destination == "dates":

        service_id = (
            state_manager.get_data(
                user_id,
                "service_id",
            )
        )

        gender = (
            state_manager.get_data(
                user_id,
                "gender",
            )
        )

        dates = (
            state_manager.get_data(
                user_id,
                "dates",
                [],
            )
        )

        state_manager.set_state(
            user_id,
            BOOKING_DATE,
        )

        await send_callback_message(
            query,
            (
                "📅 لطفاً تاریخ موردنظر "
                "را انتخاب کنید:\n\n"
                "❌ تاریخ‌های تکمیل‌شده "
                "قابل انتخاب نیستند."
            ),
            components=booking_dates_keyboard(
                dates,
                service_id=service_id,
                gender=gender,
            ),
        )

        return


# =========================================================
# Other Person Registration
# =========================================================

async def process_booking_message(
    message: Message,
) -> bool:

    user_id = message.author.id

    state = (
        state_manager.get_state(
            user_id
        )
    )

    if state is None:
        return False

    value = (
        message.text or ""
    ).strip()

    if not value:
        return True

    # Cancel booking flow.

    if (
        value in (
            "لغو",
            "انصراف",
            "/cancel",
        )
        and (
            state.startswith(
                "booking_"
            )
        )
    ):

        state_manager.clear_state(
            user_id
        )

        await message.reply(
            "فرآیند دریافت نوبت لغو شد.",
            components=main_keyboard(),
        )

        return True

    # -----------------------------------------------------
    # Other person - Name
    # -----------------------------------------------------

    if state == OTHER_PATIENT_NAME:

        normalized = (
            " ".join(
                value.split()
            )
        )

        if not validate_full_name(
            normalized
        ):

            await message.reply(
                "نام و نام خانوادگی معتبر نیست.\n"
                "مثال: علی رضایی"
            )

            return True

        parts = (
            normalized.split()
        )

        state_manager.set_data(
            user_id,
            "other_first_name",
            parts[0],
        )

        state_manager.set_data(
            user_id,
            "other_last_name",
            " ".join(
                parts[1:]
            ),
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_NATIONAL_ID,
        )

        await message.reply(
            "لطفاً کد ملی ۱۰ رقمی فرد را وارد کنید:"
        )

        return True

    # -----------------------------------------------------
    # Other person - National ID
    # -----------------------------------------------------

    if state == OTHER_PATIENT_NATIONAL_ID:

        if not validate_national_id(
            value
        ):

            await message.reply(
                "کد ملی واردشده معتبر نیست.\n"
                "لطفاً دوباره وارد کنید."
            )

            return True

        state_manager.set_data(
            user_id,
            "other_national_id",
            value,
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_PHONE,
        )

        await message.reply(
            "لطفاً شماره موبایل فرد را وارد کنید:\n"
            "مثال: 09123456789"
        )

        return True

    # -----------------------------------------------------
    # Other person - Phone
    # -----------------------------------------------------

    if state == OTHER_PATIENT_PHONE:

        if not validate_phone_number(
            value
        ):

            await message.reply(
                "شماره موبایل معتبر نیست.\n"
                "لطفاً دوباره وارد کنید."
            )

            return True

        state_manager.set_data(
            user_id,
            "other_phone",
            value,
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_GENDER,
        )

        await message.reply(
            "لطفاً جنسیت فرد را انتخاب کنید:",
            components=gender_keyboard(),
        )

        return True

    # -----------------------------------------------------
    # Other person - Gender
    # -----------------------------------------------------

    if state == OTHER_PATIENT_GENDER:

        if value not in GENDER_MAP:

            await message.reply(
                "لطفاً یکی از گزینه‌های آقا "
                "یا خانم را انتخاب کنید.",
                components=gender_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "other_gender",
            GENDER_MAP[value],
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_INSURANCE,
        )

        await message.reply(
            "لطفاً بیمه فرد را انتخاب کنید:",
            components=insurance_keyboard(),
        )

        return True

    # -----------------------------------------------------
    # Other person - Insurance
    # -----------------------------------------------------

    if state == OTHER_PATIENT_INSURANCE:

        if value not in INSURANCE_MAP:

            await message.reply(
                "لطفاً یکی از گزینه‌های "
                "بیمه را انتخاب کنید.",
                components=insurance_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "other_insurance",
            INSURANCE_MAP[value],
        )

        data = (
            state_manager.get_all_data(
                user_id
            )
        )

        existing = (
            repository.get_patient_by_national_id(
                data[
                    "other_national_id"
                ]
            )
        )

        if existing:

            patient_id = existing[
                "id"
            ]

        else:

            try:

                patient_id = (
                    repository.create_patient(
                        user_id=None,
                        national_id=data[
                            "other_national_id"
                        ],
                        first_name=data[
                            "other_first_name"
                        ],
                        last_name=data[
                            "other_last_name"
                        ],
                        phone_number=data[
                            "other_phone"
                        ],
                        birth_date=None,
                        gender=data[
                            "other_gender"
                        ],
                        insurance=data[
                            "other_insurance"
                        ],
                    )
                )

            except Exception:

                await message.reply(
                    (
                        "❌ هنگام ثبت اطلاعات "
                        "فرد مشکلی پیش آمد.\n"
                        "لطفاً دوباره تلاش کنید."
                    ),
                    components=main_keyboard(),
                )

                state_manager.clear_state(
                    user_id
                )

                return True

        user = (
            repository.get_user_by_bale_id(
                user_id
            )
        )

        if user is None:

            state_manager.clear_state(
                user_id
            )

            await message.reply(
                "اطلاعات کاربری شما پیدا نشد.",
                components=main_keyboard(),
            )

            return True

        repository.add_patient_profile(
            user["id"],
            patient_id,
        )

        state_manager.set_context(
            user_id,
            "selected_patient_id",
            patient_id,
        )

        state_manager.set_data(
            user_id,
            "booking_patient_id",
            patient_id,
        )

        state_manager.set_data(
            user_id,
            "booking_target",
            "other",
        )

        await show_services(
            message,
            user_id,
        )

        return True

    # -----------------------------------------------------
    # Normal booking states
    # -----------------------------------------------------

    if state in (
        BOOKING_SERVICE,
        BOOKING_GENDER,
        BOOKING_DATE,
        BOOKING_TIME,
    ):

        await message.reply(
            "لطفاً انتخاب خود را از "
            "طریق دکمه‌های نمایش‌داده‌شده "
            "انجام دهید."
        )

        return True

    return False


# =========================================================
# Legacy Compatibility
# =========================================================

async def handle_date_selection(
    message: Message,
):

    await message.reply(
        "انتخاب تاریخ از طریق دکمه‌های "
        "داخل پیام انجام می‌شود."
    )


async def handle_time_selection(
    message: Message,
):

    await message.reply(
        "انتخاب ساعت از طریق دکمه‌های "
        "داخل پیام انجام می‌شود."
    )


async def handle_booking_confirmation(
    message: Message,
):

    await message.reply(
        "ثبت نوبت پس از انتخاب ساعت "
        "انجام می‌شود."
    )