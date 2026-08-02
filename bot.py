from bale import Bot

from config.config import BALE_TOKEN

from database.migrations import (
    run_migrations,
)

from database.seed import (
    seed,
)

from database.repository import (
    repository,
)

from handlers.start import (
    handle_start,
)

from handlers.patients import (
    handle_patient_registration,
    handle_patient_lookup,
    process_registration_message,
    handle_patient_edit,
)

from handlers.appointments import (
    handle_my_appointments,
    handle_cancel_appointment,
    process_cancel_appointment,
)

from handlers.booking import (
    handle_booking_start,
    handle_date_selection,
    handle_time_selection,
    handle_booking_confirmation,
    process_booking_message,
)

from handlers.callbacks import (
    handle_callback,
)

from handlers.admin import (
    handle_admin_panel,
    handle_pending_appointments,
    handle_manage_schedule,
    handle_manage_patients,
)

from utils.state_manager import (
    state_manager,
)

from utils.keyboards import (
    main_keyboard,
)

from utils.logger import (
    logger,
)


# =========================================================
# Database Initialization
# =========================================================

run_migrations()

seed(
    create_test_slots=True
)


# =========================================================
# Bot
# =========================================================

bot = Bot(
    token=BALE_TOKEN
)


# =========================================================
# Clinic Information
# =========================================================

async def handle_clinic_info(
    message,
):

    clinic_name = (
        repository.get_setting(
            "clinic_name"
        )
        or "درمانگاه فرهنگیان"
    )

    phone = (
        repository.get_setting(
            "clinic_phone"
        )
        or "ثبت نشده"
    )

    address = (
        repository.get_setting(
            "clinic_address"
        )
        or "ثبت نشده"
    )

    working_hours = (
        repository.get_setting(
            "working_hours"
        )
        or "ثبت نشده"
    )

    await message.reply(
        "🏥 اطلاعات درمانگاه\n\n"
        f"نام: {clinic_name}\n"
        f"تلفن: {phone}\n"
        f"آدرس: {address}\n"
        f"ساعات نوبت‌دهی: "
        f"{working_hours}\n\n"
        "جمعه‌ها درمانگاه تعطیل است.",
        components=main_keyboard(),
    )


# =========================================================
# Ready
# =========================================================

@bot.event
async def on_ready():

    logger.info(
        "Bale connection established successfully."
    )

    if bot.user:

        logger.info(
            "Bot identity verified: @%s",
            bot.user.username,
        )


# =========================================================
# Message
# =========================================================

@bot.event
async def on_message(
    message,
):

    if not message.text:
        return

    text = (
        message.text.strip()
    )

    user_id = (
        message.author.id
    )

    # =====================================================
    # Commands
    # =====================================================

    if text == "/start":

        await handle_start(
            message
        )

        return

    if text == "/register":

        await handle_patient_registration(
            message
        )

        return

    if text == "/patient":

        await handle_patient_lookup(
            message
        )

        return

    if text == "/appointments":

        await handle_my_appointments(
            message
        )

        return

    if text == "/cancel":

        await handle_cancel_appointment(
            message
        )

        return

    if text == "/book":

        await handle_booking_start(
            message
        )

        return

    if text == "/date":

        await handle_date_selection(
            message
        )

        return

    if text == "/time":

        await handle_time_selection(
            message
        )

        return

    if text == "/confirm":

        await handle_booking_confirmation(
            message
        )

        return

    # =====================================================
    # Main Menu
    # =====================================================

    if text == "دریافت نوبت":

        await handle_booking_start(
            message
        )

        return

    if text == "نوبت‌های من":

        await handle_my_appointments(
            message
        )

        return

    if text == "اطلاعات بیمار":

        await handle_patient_lookup(
            message
        )

        return

    if text == "اطلاعات درمانگاه":

        await handle_clinic_info(
            message
        )

        return

    # =====================================================
    # Patient Submenu
    # =====================================================

    if text in (
        "ویرایش اطلاعات بیمار",
        "ویرایش اطلاعات",
    ):

        await handle_patient_edit(
            message
        )

        return

    if text == "بازگشت به خانه":

        state_manager.clear_state(
            user_id
        )

        await message.reply(
            "به منوی اصلی بازگشتید.",
            components=main_keyboard(),
        )

        return

    # =====================================================
    # Admin
    # =====================================================

    if text == "/admin":

        await handle_admin_panel(
            message
        )

        return

    if text == "/pending":

        await handle_pending_appointments(
            message
        )

        return

    if text == "/schedule":

        await handle_manage_schedule(
            message
        )

        return

    if text == "/patients":

        await handle_manage_patients(
            message
        )

        return

    # =====================================================
    # State Handling
    # =====================================================

    state = (
        state_manager.get_state(
            user_id
        )
    )

    if state is None:
        return

    # -----------------------------------------------------
    # Booking
    # -----------------------------------------------------

    handled = (
        await process_booking_message(
            message
        )
    )

    if handled:
        return

    # -----------------------------------------------------
    # Cancel Appointment
    # -----------------------------------------------------

    handled = (
        await process_cancel_appointment(
            message
        )
    )

    if handled:
        return

    # -----------------------------------------------------
    # Patient Registration / Edit
    # -----------------------------------------------------

    handled = (
        await process_registration_message(
            message
        )
    )

    if handled:
        return


# =========================================================
# Callback
# =========================================================

@bot.event
async def on_callback(
    query,
):

    await handle_callback(
        query
    )


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    logger.info(
        "Starting ClinicBot..."
    )

    bot.run()