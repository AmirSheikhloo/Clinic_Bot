from datetime import date

from bale import (
    Message,
    CallbackQuery,
)

from database.repository import repository

from utils.state_manager import state_manager

from utils.helpers import (
    to_date_label,
)

from utils.keyboards import (
    appointments_menu_keyboard,
    appointment_list_keyboard,
    appointment_detail_keyboard,
    cancel_confirmation_keyboard,
    cancel_success_home_keyboard,
    main_keyboard,
)


CANCEL_APPOINTMENT = "cancel_appointment"


# =========================================================
# Helpers
# =========================================================

def get_tracking_code(
    appointment_id: int,
) -> str:

    return f"CF-{appointment_id:06d}"


def can_cancel_appointment(
    appointment,
) -> bool:

    if appointment is None:
        return False

    if appointment.get("status") != "scheduled":
        return False

    try:

        appointment_date = date.fromisoformat(
            appointment.get(
                "appointment_date"
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return False

    return appointment_date > date.today()


def appointment_status_text(
    status: str,
) -> str:

    status_names = {
        "scheduled": "ثبت شده",
        "completed": "انجام شده",
        "cancelled": "لغو شده",
        "no_show": "عدم مراجعه",
    }

    return status_names.get(
        status,
        status,
    )


def appointment_details_text(
    appointment,
) -> str:

    return (
        "📋 جزئیات نوبت\n\n"
        f"🔖 کد پیگیری: "
        f"{get_tracking_code(appointment.get('id'))}\n"
        f"🏥 خدمت: "
        f"{appointment.get('service_name')}\n"
        f"📅 تاریخ: "
        f"{to_date_label(appointment.get('appointment_date'))}\n"
        f"🕐 ساعت: "
        f"{appointment.get('start_time')}\n"
        f"👤 بیمار: "
        f"{appointment.get('patient_first_name') or ''} "
        f"{appointment.get('patient_last_name') or ''}\n"
        f"📌 وضعیت: "
        f"{appointment_status_text(appointment.get('status'))}"
    )


async def send_callback_message(
    query: CallbackQuery,
    text: str,
    components=None,
) -> None:

    if query.message is None:
        return

    bot = query.message.get_bot()

    await bot.send_message(
        query.message.chat_id,
        text,
        components=components,
    )

    try:

        await query.message.delete()

    except Exception:

        pass


async def get_user_appointment(
    query: CallbackQuery,
    appointment_id: int,
):

    bale_user_id = query.user.id

    user = repository.get_user_by_bale_id(
        bale_user_id
    )

    if user is None:
        return None

    return repository.get_user_appointment(
        user_id=user["id"],
        appointment_id=appointment_id,
    )


# =========================================================
# Main - My Appointments
# =========================================================

async def handle_my_appointments(
    message: Message,
) -> None:

    user_id = message.author.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        await message.reply(
            "اطلاعات کاربری شما پیدا نشد.\n"
            "لطفاً ابتدا /start را بزنید."
        )

        return

    current_appointments = (
        repository.get_current_appointments_for_user(
            user["id"]
        )
    )

    if not current_appointments:

        await message.reply(
            "📋 نوبت‌های من\n\n"
            "شما در حال حاضر نوبت فعالی ندارید.",
            components=appointments_menu_keyboard(),
        )

        return

    await message.reply(
        "📋 نوبت‌های من\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        components=appointments_menu_keyboard(),
    )


# =========================================================
# Callback Router
# =========================================================

async def handle_appointment_callback(
    query: CallbackQuery,
) -> None:

    data = query.data or ""

    if not data:
        return

    if data == "appointments:menu":

        await send_callback_message(
            query,
            (
                "📋 نوبت‌های من\n\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
            ),
            components=appointments_menu_keyboard(),
        )

        return

    if data == "appointments:current":

        await handle_current_appointments_callback(
            query
        )

        return

    if data == "appointments:history":

        await handle_appointment_history_callback(
            query
        )

        return

    if data == "appointments:home":

        state_manager.clear_state(
            query.user.id
        )

        await send_callback_message(
            query,
            (
                "🌿 به سامانه نوبت‌دهی درمانگاه طب سنتی حضرت ابوالفضل خوش آمدید 🌿\n\n"
                "لطفاً برای ادامه، یکی از گزینه‌های زیر را انتخاب کنید:"
            ),
            components=main_keyboard(),
        )

        return

    if data.startswith(
        "appointment_current:"
    ):

        await handle_appointment_detail_callback(
            query,
            prefix="appointment_current:",
        )

        return

    if data.startswith(
        "appointment_history:"
    ):

        await handle_appointment_detail_callback(
            query,
            prefix="appointment_history:",
        )

        return

    if data.startswith(
        "appointment_cancel:"
    ):

        await handle_appointment_cancel_callback(
            query
        )

        return

    if data.startswith(
        "appointment_cancel_confirm:"
    ):

        await handle_appointment_cancel_confirm_callback(
            query
        )

        return

    if data.startswith(
        "appointment_cancel_abort:"
    ):

        await handle_appointment_cancel_abort_callback(
            query
        )

        return


# =========================================================
# Current Appointments
# =========================================================

async def handle_current_appointments_callback(
    query: CallbackQuery,
) -> None:

    user_id = query.user.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        await send_callback_message(
            query,
            "اطلاعات کاربری شما پیدا نشد.",
            components=main_keyboard(),
        )

        return

    appointments = (
        repository.get_current_appointments_for_user(
            user["id"]
        )
    )

    if not appointments:

        await send_callback_message(
            query,
            (
                "📋 نوبت‌های جاری\n\n"
                "شما در حال حاضر نوبت فعالی ندارید."
            ),
            components=appointments_menu_keyboard(),
        )

        return

    await send_callback_message(
        query,
        (
            "📋 نوبت‌های جاری\n\n"
            "برای مشاهده جزئیات، نوبت موردنظر را انتخاب کنید:"
        ),
        components=appointment_list_keyboard(
            appointments,
            prefix="appointment_current",
        ),
    )


# =========================================================
# History
# =========================================================

async def handle_appointment_history_callback(
    query: CallbackQuery,
) -> None:

    user_id = query.user.id

    user = repository.get_user_by_bale_id(
        user_id
    )

    if user is None:

        await send_callback_message(
            query,
            "اطلاعات کاربری شما پیدا نشد.",
            components=main_keyboard(),
        )

        return

    appointments = (
        repository.get_appointment_history_for_user(
            user["id"]
        )
    )

    if not appointments:

        await send_callback_message(
            query,
            (
                "📜 تاریخچه نوبت‌ها\n\n"
                "تاریخچه‌ای برای نمایش وجود ندارد."
            ),
            components=appointments_menu_keyboard(),
        )

        return

    await send_callback_message(
        query,
        (
            "📜 تاریخچه نوبت‌ها\n\n"
            "برای مشاهده جزئیات، نوبت موردنظر را انتخاب کنید:"
        ),
        components=appointment_list_keyboard(
            appointments,
            prefix="appointment_history",
        ),
    )


# =========================================================
# Detail
# =========================================================

async def handle_appointment_detail_callback(
    query: CallbackQuery,
    prefix: str,
) -> None:

    data = query.data or ""

    try:

        appointment_id = int(
            data.split(
                prefix,
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        return

    appointment = await get_user_appointment(
        query,
        appointment_id,
    )

    if appointment is None:

        await send_callback_message(
            query,
            (
                "این نوبت پیدا نشد یا دیگر "
                "دسترسی به آن امکان‌پذیر نیست."
            ),
            components=appointments_menu_keyboard(),
        )

        return

    can_cancel = can_cancel_appointment(
        appointment
    )

    text = appointment_details_text(
        appointment
    )

    if (
        appointment.get("status") == "scheduled"
        and not can_cancel
    ):

        try:

            appointment_date = date.fromisoformat(
                appointment.get(
                    "appointment_date"
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            appointment_date = None

        if (
            appointment_date is not None
            and appointment_date <= date.today()
        ):

            text += (
                "\n\n"
                "⚠️ این نوبت دیگر قابل لغو نیست."
            )

    await send_callback_message(
        query,
        text,
        components=appointment_detail_keyboard(
            appointment_id=appointment.get("id"),
            can_cancel=can_cancel,
        ),
    )


# =========================================================
# Cancel - Request
# =========================================================

async def handle_appointment_cancel_callback(
    query: CallbackQuery,
) -> None:

    data = query.data or ""

    try:

        appointment_id = int(
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

    appointment = await get_user_appointment(
        query,
        appointment_id,
    )

    if appointment is None:

        await send_callback_message(
            query,
            "این نوبت پیدا نشد.",
            components=appointments_menu_keyboard(),
        )

        return

    if appointment.get("status") != "scheduled":

        await send_callback_message(
            query,
            (
                "این نوبت دیگر فعال نیست و "
                "قابل لغو نمی‌باشد."
            ),
            components=appointment_detail_keyboard(
                appointment_id,
                can_cancel=False,
            ),
        )

        return

    if not can_cancel_appointment(
        appointment
    ):

        await send_callback_message(
            query,
            (
                "⚠️ لغو این نوبت امکان‌پذیر نیست.\n\n"
                "لغو نوبت فقط تا یک روز قبل از "
                "تاریخ نوبت امکان‌پذیر است."
            ),
            components=appointment_detail_keyboard(
                appointment_id,
                can_cancel=False,
            ),
        )

        return

    await send_callback_message(
        query,
        (
            "⚠️ لغو نوبت\n\n"
            f"🏥 خدمت: {appointment.get('service_name')}\n"
            f"📅 تاریخ: "
            f"{to_date_label(appointment.get('appointment_date'))}\n"
            f"🕐 ساعت: "
            f"{appointment.get('start_time')}\n\n"
            "آیا از لغو این نوبت مطمئن هستید؟"
        ),
        components=cancel_confirmation_keyboard(
            appointment_id
        ),
    )


# =========================================================
# Cancel - Confirm
# =========================================================

async def handle_appointment_cancel_confirm_callback(
    query: CallbackQuery,
) -> None:

    data = query.data or ""

    try:

        appointment_id = int(
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

    appointment = await get_user_appointment(
        query,
        appointment_id,
    )

    if appointment is None:

        await send_callback_message(
            query,
            "این نوبت پیدا نشد.",
            components=appointments_menu_keyboard(),
        )

        return

    if appointment.get("status") != "scheduled":

        await send_callback_message(
            query,
            (
                "این نوبت دیگر فعال نیست و "
                "قابل لغو نمی‌باشد."
            ),
            components=appointments_menu_keyboard(),
        )

        return

    if not can_cancel_appointment(
        appointment
    ):

        await send_callback_message(
            query,
            "⚠️ زمان مجاز لغو این نوبت گذشته است.",
            components=appointment_detail_keyboard(
                appointment_id,
                can_cancel=False,
            ),
        )

        return

    try:

        repository.cancel_appointment(
            appointment_id
        )

    except Exception:

        await send_callback_message(
            query,
            (
                "❌ هنگام لغو نوبت مشکلی پیش آمد.\n"
                "لطفاً دوباره تلاش کنید."
            ),
            components=appointments_menu_keyboard(),
        )

        return

    state_manager.clear_state(
        query.user.id
    )

    await send_callback_message(
        query,
        (
            "✅ نوبت شما با موفقیت لغو شد.\n\n"
            f"🔖 کد پیگیری: "
            f"{get_tracking_code(appointment.get('id'))}\n"
            f"🏥 خدمت: "
            f"{appointment.get('service_name')}\n"
            f"📅 تاریخ: "
            f"{to_date_label(appointment.get('appointment_date'))}\n"
            f"🕐 ساعت: "
            f"{appointment.get('start_time')}"
        ),
        components=cancel_success_home_keyboard(),
    )


# =========================================================
# Cancel - Abort
# =========================================================

async def handle_appointment_cancel_abort_callback(
    query: CallbackQuery,
) -> None:

    data = query.data or ""

    try:

        appointment_id = int(
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

    appointment = await get_user_appointment(
        query,
        appointment_id,
    )

    if appointment is None:

        await send_callback_message(
            query,
            "این نوبت پیدا نشد.",
            components=appointments_menu_keyboard(),
        )

        return

    await send_callback_message(
        query,
        appointment_details_text(
            appointment
        ),
        components=appointment_detail_keyboard(
            appointment_id=appointment.get("id"),
            can_cancel=can_cancel_appointment(
                appointment
            ),
        ),
    )


# =========================================================
# Legacy / Compatibility
# =========================================================

async def handle_cancel_appointment(
    message: Message,
) -> None:

    await handle_my_appointments(
        message
    )


async def process_cancel_appointment(
    message: Message,
) -> bool:

    if (
        state_manager.get_state(
            message.author.id
        )
        != CANCEL_APPOINTMENT
    ):

        return False

    state_manager.clear_state(
        message.author.id
    )

    await message.reply(
        "لغو نوبت از طریق بخش «نوبت‌های من» انجام می‌شود.",
        components=appointments_menu_keyboard(),
    )

    return True