from bale import (
    Message,
    CallbackQuery,
)

from database.repository import repository
from services.schedule_service import schedule_service

from utils.keyboards import (
    main_keyboard,
    patient_keyboard,
    booking_services_keyboard,
)

from utils.state_manager import state_manager

from utils.validators import (
    validate_full_name,
    validate_national_id,
    validate_phone_number,
)


# ==============================
# Registration states
# ==============================

REGISTRATION_NAME = "registration_name"
REGISTRATION_NATIONAL_ID = "registration_national_id"
REGISTRATION_PHONE = "registration_phone"
REGISTRATION_GENDER = "registration_gender"
REGISTRATION_INSURANCE = "registration_insurance"


# ==============================
# Other patient booking states
# ==============================

OTHER_PATIENT_NAME = "other_patient_name"
OTHER_PATIENT_NATIONAL_ID = "other_patient_national_id"
OTHER_PATIENT_PHONE = "other_patient_phone"
OTHER_PATIENT_GENDER = "other_patient_gender"
OTHER_PATIENT_INSURANCE = "other_patient_insurance"


# ==============================
# Edit states
# ==============================

EDIT_NAME = "edit_name"
EDIT_PHONE = "edit_phone"
EDIT_GENDER = "edit_gender"
EDIT_INSURANCE = "edit_insurance"


# ==============================
# Insurance options
# ==============================

INSURANCE_OPTIONS = {
    "سلامت": "health",
    "تامین اجتماعی": "social_security",
    "نیروهای مسلح": "armed_forces",
    "بدون بیمه": "none",
}


INSURANCE_DISPLAY = {
    "health": "سلامت",
    "social_security": "تامین اجتماعی",
    "armed_forces": "نیروهای مسلح",
    "none": "بدون بیمه",
}


# ==============================
# Gender options
# ==============================

GENDER_OPTIONS = {
    "آقا": "male",
    "خانم": "female",
}


GENDER_DISPLAY = {
    "male": "آقا",
    "female": "خانم",
}


# ==============================
# Registration
# ==============================

async def handle_patient_registration(
    message: Message,
) -> None:

    user_id = message.author.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        repository.create_user(
            bale_user_id=user_id,
            username=message.author.username,
            first_name=message.author.first_name,
            last_name=message.author.last_name,
        )

        user = repository.get_user_by_bale_id(
            user_id
        )

    if user is None:

        await message.reply(
            "متأسفانه هنگام ایجاد حساب کاربری مشکلی پیش آمد. "
            "لطفاً دوباره تلاش کنید."
        )

        return

    patient = repository.get_patient_by_user_id(
        user["id"]
    )

    if patient is not None:

        await message.reply(
            "اطلاعات بیمار شما قبلاً ثبت شده است.",
            components=main_keyboard(),
        )

        return

    state_manager.clear_state(
        user_id
    )

    state_manager.set_state(
        user_id,
        REGISTRATION_NAME,
    )

    await message.reply(
        "لطفاً نام و نام خانوادگی خود را وارد کنید.\n\n"
        "مثال: علی رضایی\n\n"
        "برای لغو فرایند، عبارت «لغو» را ارسال کنید."
    )


# ==============================
# Other Patient Registration
# ==============================

async def start_other_patient_registration(
    query: CallbackQuery,
) -> None:

    user_id = query.user.id

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

    if query.message is None:
        return

    bot = query.message.get_bot()

    try:
        await query.message.delete()
    except Exception:
        pass

    await bot.send_message(
        query.message.chat_id,
        (
            "👥 ثبت اطلاعات بیمار\n\n"
            "لطفاً نام و نام خانوادگی شخصی که می‌خواهید "
            "برای او نوبت بگیرید را وارد کنید.\n\n"
            "مثال: علی رضایی\n\n"
            "اطلاعات این شخص فقط برای ثبت همین نوبت استفاده می‌شود "
            "و به‌عنوان پروفایل جداگانه برای او ایجاد نمی‌شود.\n\n"
            "برای لغو فرایند، عبارت «لغو» را ارسال کنید."
        ),
    )


# ==============================
# Registration message processor
# ==============================

async def process_registration_message(
    message: Message,
) -> bool:

    user_id = message.author.id
    state = state_manager.get_state(
        user_id
    )

    if state is None:
        return False

    value = (
        message.text or ""
    ).strip()

    # ==============================
    # Cancel
    # ==============================

    if value in (
        "لغو",
        "انصراف",
        "/cancel",
    ):

        state_manager.clear_state(
            user_id
        )

        await message.reply(
            "فرایند لغو شد و اطلاعات جدیدی ذخیره نشد.",
            components=main_keyboard(),
        )

        return True

    if not value:

        await message.reply(
            "لطفاً یک مقدار معتبر وارد کنید."
        )

        return True


    # =====================================================
    # Other patient registration
    # =====================================================

    if state in (
        OTHER_PATIENT_NAME,
        OTHER_PATIENT_NATIONAL_ID,
        OTHER_PATIENT_PHONE,
        OTHER_PATIENT_GENDER,
        OTHER_PATIENT_INSURANCE,
    ):

        return await process_other_patient_registration(
            message,
            state,
            value,
        )


    # --------------------------------
    # Name + Last name
    # --------------------------------

    if state == REGISTRATION_NAME:

        normalized_name = " ".join(
            value.split()
        )

        parts = normalized_name.split(
            " "
        )

        if len(parts) < 2:

            await message.reply(
                "لطفاً نام و نام خانوادگی خود را وارد کنید.\n\n"
                "مثال: علی رضایی"
            )

            return True

        if not validate_full_name(
            normalized_name
        ):

            await message.reply(
                "نام و نام خانوادگی واردشده صحیح نیست.\n"
                "لطفاً فقط حروف فارسی یا انگلیسی وارد کنید و از وارد کردن "
                "عدد یا علامت‌های غیرضروری خودداری کنید.\n\n"
                "مثال: علی رضایی"
            )

            return True

        first_name = parts[0]
        last_name = " ".join(
            parts[1:]
        )

        state_manager.set_data(
            user_id,
            "first_name",
            first_name,
        )

        state_manager.set_data(
            user_id,
            "last_name",
            last_name,
        )

        state_manager.set_state(
            user_id,
            REGISTRATION_NATIONAL_ID,
        )

        await message.reply(
            "لطفاً کد ملی ۱۰ رقمی خود را وارد کنید.\n\n"
            "مثال: 0012345678"
        )

        return True


    # --------------------------------
    # National ID
    # --------------------------------

    if state == REGISTRATION_NATIONAL_ID:

        if not validate_national_id(
            value
        ):

            await message.reply(
                "کد ملی واردشده صحیح نیست.\n"
                "کد ملی باید دقیقاً ۱۰ رقم باشد.\n\n"
                "لطفاً دوباره وارد کنید."
            )

            return True

        existing_patient = (
            repository.get_patient_by_national_id(
                value
            )
        )

        if existing_patient is not None:

            await message.reply(
                "این کد ملی قبلاً در سامانه ثبت شده است.\n"
                "اگر فکر می‌کنید اشتباهی رخ داده، لطفاً با درمانگاه تماس بگیرید."
            )

            state_manager.clear_state(
                user_id
            )

            return True

        state_manager.set_data(
            user_id,
            "national_id",
            value,
        )

        state_manager.set_state(
            user_id,
            REGISTRATION_PHONE,
        )

        await message.reply(
            "لطفاً شماره موبایل خود را وارد کنید.\n\n"
            "شماره باید با 09 شروع شود و ۱۱ رقم باشد.\n"
            "مثال: 09123456789"
        )

        return True


    # --------------------------------
    # Phone
    # --------------------------------

    if state == REGISTRATION_PHONE:

        if not validate_phone_number(
            value
        ):

            await message.reply(
                "شماره موبایل واردشده صحیح نیست.\n"
                "شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.\n\n"
                "مثال: 09123456789"
            )

            return True

        state_manager.set_data(
            user_id,
            "phone_number",
            value,
        )

        state_manager.set_state(
            user_id,
            REGISTRATION_GENDER,
        )

        await message.reply(
            "لطفاً جنسیت خود را انتخاب کنید.",
            components=gender_keyboard(),
        )

        return True


    # --------------------------------
    # Gender
    # --------------------------------

    if state == REGISTRATION_GENDER:

        if value not in GENDER_OPTIONS:

            await message.reply(
                "لطفاً جنسیت خود را فقط از بین گزینه‌های «آقا» یا «خانم» انتخاب کنید.",
                components=gender_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "gender",
            GENDER_OPTIONS[value],
        )

        state_manager.set_state(
            user_id,
            REGISTRATION_INSURANCE,
        )

        await message.reply(
            "لطفاً بیمه خود را انتخاب کنید.",
            components=insurance_keyboard(),
        )

        return True


    # --------------------------------
    # Insurance
    # --------------------------------

    if state == REGISTRATION_INSURANCE:

        if value not in INSURANCE_OPTIONS:

            await message.reply(
                "لطفاً بیمه خود را فقط از بین گزینه‌های نمایش‌داده‌شده انتخاب کنید.",
                components=insurance_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "insurance",
            INSURANCE_OPTIONS[value],
        )

        data = state_manager.get_all_data(
            user_id
        )

        user = repository.get_user_by_bale_id(
            user_id
        )

        if user is None:

            await message.reply(
                "متأسفانه اطلاعات کاربری شما پیدا نشد.\n"
                "لطفاً دوباره ثبت‌نام را شروع کنید."
            )

            state_manager.clear_state(
                user_id
            )

            return True

        try:

            repository.create_patient(
                user_id=user["id"],
                national_id=data["national_id"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone_number=data["phone_number"],
                birth_date=None,
                gender=data["gender"],
                insurance=data["insurance"],
            )

            repository.update_user_phone(
                bale_user_id=user_id,
                phone_number=data["phone_number"],
            )

        except Exception:

            await message.reply(
                "متأسفانه هنگام ثبت اطلاعات مشکلی پیش آمد.\n"
                "لطفاً دوباره تلاش کنید."
            )

            logger_exception()

            state_manager.clear_state(
                user_id
            )

            return True

        state_manager.clear_state(
            user_id
        )

        await message.reply(
            "اطلاعات شما با موفقیت ثبت شد.\n\n"
            "اکنون می‌توانید از منوی اصلی خدمات موردنظر خود را انتخاب کنید.",
            components=main_keyboard(),
        )

        return True


    # --------------------------------
    # Edit
    # --------------------------------

    return await process_edit_message(
        message,
        state,
        value,
    )


# =========================================================
# Other Patient Registration Processor
# =========================================================

async def process_other_patient_registration(
    message: Message,
    state: str,
    value: str,
) -> bool:

    user_id = message.author.id


    # --------------------------------
    # Name
    # --------------------------------

    if state == OTHER_PATIENT_NAME:

        normalized_name = " ".join(
            value.split()
        )

        parts = normalized_name.split(
            " "
        )

        if len(parts) < 2:

            await message.reply(
                "لطفاً نام و نام خانوادگی شخص را وارد کنید.\n\n"
                "مثال: علی رضایی"
            )

            return True

        if not validate_full_name(
            normalized_name
        ):

            await message.reply(
                "نام و نام خانوادگی واردشده صحیح نیست.\n"
                "لطفاً فقط حروف فارسی یا انگلیسی وارد کنید."
            )

            return True

        state_manager.set_data(
            user_id,
            "other_first_name",
            parts[0],
        )

        state_manager.set_data(
            user_id,
            "other_last_name",
            " ".join(parts[1:]),
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_NATIONAL_ID,
        )

        await message.reply(
            "لطفاً کد ملی ۱۰ رقمی این شخص را وارد کنید.\n\n"
            "مثال: 0012345678"
        )

        return True


    # --------------------------------
    # National ID
    # --------------------------------

    if state == OTHER_PATIENT_NATIONAL_ID:

        if not validate_national_id(
            value
        ):

            await message.reply(
                "کد ملی واردشده صحیح نیست.\n"
                "کد ملی باید دقیقاً ۱۰ رقم باشد."
            )

            return True

        existing_patient = (
            repository.get_patient_by_national_id(
                value
            )
        )

        if existing_patient is not None:

            await message.reply(
                "این کد ملی قبلاً در سامانه ثبت شده است.\n\n"
                "برای حفظ اطلاعات ثبت‌شده، امکان ساخت اطلاعات جدید "
                "برای این کد ملی وجود ندارد."
            )

            state_manager.clear_state(
                user_id
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
            "لطفاً شماره موبایل این شخص را وارد کنید.\n\n"
            "مثال: 09123456789"
        )

        return True


    # --------------------------------
    # Phone
    # --------------------------------

    if state == OTHER_PATIENT_PHONE:

        if not validate_phone_number(
            value
        ):

            await message.reply(
                "شماره موبایل واردشده صحیح نیست.\n"
                "شماره باید ۱۱ رقم باشد و با 09 شروع شود."
            )

            return True

        state_manager.set_data(
            user_id,
            "other_phone_number",
            value,
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_GENDER,
        )

        await message.reply(
            "لطفاً جنسیت این شخص را انتخاب کنید.",
            components=gender_keyboard(),
        )

        return True


    # --------------------------------
    # Gender
    # --------------------------------

    if state == OTHER_PATIENT_GENDER:

        if value not in GENDER_OPTIONS:

            await message.reply(
                "لطفاً جنسیت را فقط از بین گزینه‌های «آقا» یا «خانم» انتخاب کنید.",
                components=gender_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "other_gender",
            GENDER_OPTIONS[value],
        )

        state_manager.set_state(
            user_id,
            OTHER_PATIENT_INSURANCE,
        )

        await message.reply(
            "لطفاً بیمه این شخص را انتخاب کنید.",
            components=insurance_keyboard(),
        )

        return True


    # --------------------------------
    # Insurance
    # --------------------------------

    if state == OTHER_PATIENT_INSURANCE:

        if value not in INSURANCE_OPTIONS:

            await message.reply(
                "لطفاً بیمه را فقط از بین گزینه‌های نمایش‌داده‌شده انتخاب کنید.",
                components=insurance_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "other_insurance",
            INSURANCE_OPTIONS[value],
        )

        data = state_manager.get_all_data(
            user_id
        )

        try:

            repository.create_patient(
                user_id=None,
                national_id=data["other_national_id"],
                first_name=data["other_first_name"],
                last_name=data["other_last_name"],
                phone_number=data["other_phone_number"],
                birth_date=None,
                gender=data["other_gender"],
                insurance=data["other_insurance"],
            )

            patient = (
                repository.get_patient_by_national_id(
                    data["other_national_id"]
                )
            )

        except Exception:

            logger_exception()

            state_manager.clear_state(
                user_id
            )

            await message.reply(
                "متأسفانه هنگام ثبت اطلاعات بیمار مشکلی پیش آمد.\n"
                "لطفاً دوباره تلاش کنید.",
                components=main_keyboard(),
            )

            return True

        if patient is None:

            state_manager.clear_state(
                user_id
            )

            await message.reply(
                "اطلاعات بیمار ثبت شد، اما بازیابی اطلاعات او "
                "برای ادامه نوبت‌دهی ممکن نبود.\n"
                "لطفاً دوباره تلاش کنید.",
                components=main_keyboard(),
            )

            return True

        state_manager.clear_state(
            user_id
        )

        state_manager.set_data(
            user_id,
            "booking_target",
            "other",
        )

        state_manager.set_data(
            user_id,
            "booking_patient",
            patient,
        )

        state_manager.set_context(
            user_id,
            "selected_patient_id",
            patient["id"],
        )

        gender = patient.get(
            "gender"
        )

        services = schedule_service.get_services(
            gender=gender,
            days_ahead=7,
        )

        if not services:

            state_manager.clear_state(
                user_id
            )

            await message.reply(
                (
                    "اطلاعات بیمار ثبت شد، اما در حال حاضر "
                    "خدمتی متناسب با جنسیت این شخص برای نوبت‌دهی وجود ندارد."
                ),
                components=main_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "booking_target",
            "other",
        )

        state_manager.set_data(
            user_id,
            "booking_patient",
            patient,
        )

        state_manager.set_data(
            user_id,
            "gender",
            gender,
        )

        state_manager.set_data(
            user_id,
            "services",
            services,
        )

        from handlers.booking import BOOKING_SERVICE

        state_manager.set_state(
            user_id,
            BOOKING_SERVICE,
        )

        await message.reply(
            (
                "✅ اطلاعات بیمار دریافت شد.\n\n"
                "لطفاً خدمت موردنظر را انتخاب کنید:"
            ),
            components=booking_services_keyboard(
                services
            ),
        )

        return True

    return False


# ==============================
# Patient lookup
# ==============================

async def handle_patient_lookup(
    message: Message,
) -> None:

    user_id = message.author.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        await message.reply(
            "اطلاعات کاربری شما در سامانه پیدا نشد."
        )

        return

    patient = repository.get_patient_by_user_id(
        user["id"]
    )

    if patient is None:

        await message.reply(
            "هنوز اطلاعات بیمار شما ثبت نشده است.",
            components=main_keyboard(),
        )

        return

    gender_text = GENDER_DISPLAY.get(
        patient.get("gender"),
        "ثبت نشده",
    )

    insurance_text = INSURANCE_DISPLAY.get(
        patient.get("insurance"),
        "ثبت نشده",
    )

    await message.reply(
        "👤 اطلاعات بیمار\n\n"
        f"نام و نام خانوادگی: "
        f"{patient.get('first_name', '')} "
        f"{patient.get('last_name', '')}\n"
        f"کد ملی: {patient.get('national_id') or 'ثبت نشده'}\n"
        f"شماره موبایل: {patient.get('phone_number') or 'ثبت نشده'}\n"
        f"جنسیت: {gender_text}\n"
        f"بیمه: {insurance_text}",
        components=patient_keyboard(),
    )


# ==============================
# Patient edit
# ==============================

async def handle_patient_edit(
    message: Message,
) -> None:

    user_id = message.author.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        await message.reply(
            "اطلاعات کاربری شما در سامانه پیدا نشد."
        )

        return

    patient = repository.get_patient_by_user_id(
        user["id"]
    )

    if patient is None:

        await message.reply(
            "ابتدا باید اطلاعات بیمار خود را ثبت کنید.",
            components=main_keyboard(),
        )

        return

    state_manager.clear_state(
        user_id
    )

    state_manager.set_data(
        user_id,
        "edit_patient_id",
        patient["id"],
    )

    state_manager.set_state(
        user_id,
        EDIT_NAME,
    )

    await message.reply(
        "✏️ ویرایش اطلاعات بیمار\n\n"
        "لطفاً نام و نام خانوادگی جدید خود را وارد کنید.\n\n"
        "مثال: علی رضایی\n\n"
        "توجه: تا پایان مراحل، اطلاعات فعلی شما تغییر نمی‌کند.\n"
        "برای لغو فرایند، عبارت «لغو» را ارسال کنید."
    )


# ==============================
# Edit processor
# ==============================

async def process_edit_message(
    message: Message,
    state: str,
    value: str,
) -> bool:

    user_id = message.author.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        state_manager.clear_state(
            user_id
        )

        return False

    patient = repository.get_patient_by_user_id(
        user["id"]
    )

    if patient is None:

        state_manager.clear_state(
            user_id
        )

        return False


    # --------------------------------
    # Edit name
    # --------------------------------

    if state == EDIT_NAME:

        normalized_name = " ".join(
            value.split()
        )

        parts = normalized_name.split(
            " "
        )

        if len(parts) < 2:

            await message.reply(
                "لطفاً نام و نام خانوادگی خود را وارد کنید.\n\n"
                "مثال: علی رضایی"
            )

            return True

        if not validate_full_name(
            normalized_name
        ):

            await message.reply(
                "نام و نام خانوادگی واردشده صحیح نیست.\n"
                "لطفاً فقط حروف فارسی یا انگلیسی وارد کنید."
            )

            return True

        state_manager.set_data(
            user_id,
            "edit_first_name",
            parts[0],
        )

        state_manager.set_data(
            user_id,
            "edit_last_name",
            " ".join(parts[1:]),
        )

        state_manager.set_state(
            user_id,
            EDIT_PHONE,
        )

        await message.reply(
            "نام و نام خانوادگی دریافت شد.\n\n"
            "لطفاً شماره موبایل جدید خود را وارد کنید.\n\n"
            "مثال: 09123456789"
        )

        return True


    # --------------------------------
    # Edit phone
    # --------------------------------

    if state == EDIT_PHONE:

        if not validate_phone_number(
            value
        ):

            await message.reply(
                "شماره موبایل واردشده صحیح نیست.\n"
                "شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود."
            )

            return True

        state_manager.set_data(
            user_id,
            "edit_phone_number",
            value,
        )

        state_manager.set_state(
            user_id,
            EDIT_GENDER,
        )

        await message.reply(
            "شماره موبایل دریافت شد.\n\n"
            "لطفاً جنسیت خود را انتخاب کنید.",
            components=gender_keyboard(),
        )

        return True


    # --------------------------------
    # Edit gender
    # --------------------------------

    if state == EDIT_GENDER:

        if value not in GENDER_OPTIONS:

            await message.reply(
                "لطفاً جنسیت خود را فقط از بین گزینه‌های «آقا» یا «خانم» انتخاب کنید.",
                components=gender_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "edit_gender",
            GENDER_OPTIONS[value],
        )

        state_manager.set_state(
            user_id,
            EDIT_INSURANCE,
        )

        await message.reply(
            "جنسیت دریافت شد.\n\n"
            "لطفاً بیمه خود را انتخاب کنید.",
            components=insurance_keyboard(),
        )

        return True


    # --------------------------------
    # Edit insurance
    # --------------------------------

    if state == EDIT_INSURANCE:

        if value not in INSURANCE_OPTIONS:

            await message.reply(
                "لطفاً بیمه خود را فقط از بین گزینه‌های نمایش‌داده‌شده انتخاب کنید.",
                components=insurance_keyboard(),
            )

            return True

        state_manager.set_data(
            user_id,
            "edit_insurance",
            INSURANCE_OPTIONS[value],
        )

        data = state_manager.get_all_data(
            user_id
        )

        try:

            repository.update_patient(
                patient_id=patient["id"],
                first_name=data["edit_first_name"],
                last_name=data["edit_last_name"],
                phone_number=data["edit_phone_number"],
                birth_date=patient.get("birth_date"),
                gender=data["edit_gender"],
                insurance=data["edit_insurance"],
            )

            repository.update_user_phone(
                bale_user_id=user_id,
                phone_number=data["edit_phone_number"],
            )

        except Exception:

            logger_exception()

            state_manager.clear_state(
                user_id
            )

            await message.reply(
                "متأسفانه هنگام به‌روزرسانی اطلاعات مشکلی پیش آمد.\n"
                "اطلاعات قبلی شما بدون تغییر باقی ماند.",
                components=main_keyboard(),
            )

            return True

        state_manager.clear_state(
            user_id
        )

        await message.reply(
            "✅ اطلاعات بیمار با موفقیت به‌روزرسانی شد.",
            components=main_keyboard(),
        )

        return True


    state_manager.clear_state(
        user_id
    )

    return False


# ==============================
# Temporary helpers
# ==============================

def gender_keyboard():

    from bale import (
        MenuKeyboardButton,
        MenuKeyboardMarkup,
    )

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


def insurance_keyboard():

    from bale import (
        MenuKeyboardButton,
        MenuKeyboardMarkup,
    )

    keyboard = MenuKeyboardMarkup()

    keyboard.add(
        MenuKeyboardButton("سلامت"),
        row=1,
    )

    keyboard.add(
        MenuKeyboardButton("تامین اجتماعی"),
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


def logger_exception():

    import logging

    logging.getLogger(
        __name__
    ).exception(
        "Patient registration error"
    )