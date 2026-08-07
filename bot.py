import json
from bale import Bot

from config.config import BALE_TOKEN
from database.migrations import run_migrations
from database.seed import seed
from database.repository import repository
from api.crud import get_general_settings

from handlers.start import handle_start
from handlers.patients import (
    handle_patient_registration,
    handle_patient_lookup,
    process_registration_message,
    handle_patient_edit,
    safe_delete_previous_inline
)
from handlers.appointments import (
    handle_my_appointments,
    handle_cancel_appointment,
    process_cancel_appointment,
)
from handlers.booking import (
    handle_booking_start,
    process_booking_message,
)
from handlers.callbacks import handle_callback
from handlers.admin import (
    handle_admin_panel,
    handle_pending_appointments,
    handle_manage_schedule,
    handle_manage_patients,
)

from utils.state_manager import state_manager
from utils.keyboards import clinic_info_keyboard
from utils.helpers import send_welcome_message
from utils.logger import logger

# =========================================================
# Database Initialization
# =========================================================
run_migrations()
seed(create_test_slots=True)

# =========================================================
# Bot
# =========================================================
bot = Bot(token=BALE_TOKEN)

# =========================================================
# Clinic Information
# =========================================================
async def handle_clinic_info(message):
    settings = get_general_settings()
    name = settings.get("clinic_name", "").strip()
    address = settings.get("clinic_address", "").strip()
    phone_data = settings.get("clinic_phone", "").strip()
    working_hours = settings.get("working_hours_text", "").strip()
    
    if not working_hours:
        working_hours = settings.get("working_hours", "").strip()

    lines = []
    
    if name:
        lines.append(f"🏥 {name}\n")
    if address:
        lines.append(f"📍 آدرس: {address}\n")
        
    if phone_data:
        try:
            phones = json.loads(phone_data)
            phones = [p for p in phones if p.strip()]
        except Exception:
            phones = [p.strip() for p in phone_data.split("یا") if p.strip()]
        
        if phones:
            lines.append("📞 تلفن‌های تماس:")
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            for i, p in enumerate(phones[:5]):
                lines.append(f"{emojis[i]} {p}")
            lines.append("")
            
    if working_hours:
        lines.append(f"🕒 تایم کاری: {working_hours}")
        
    text = "\n".join(lines).strip()
    
    if not text:
        text = "اطلاعاتی ثبت نشده است."
        
    await message.reply(text, components=clinic_info_keyboard())

# =========================================================
# Ready
# =========================================================
@bot.event
async def on_ready():
    logger.info("Bale connection established successfully.")
    if bot.user:
        logger.info("Bot identity verified: @%s", bot.user.username)

# =========================================================
# Message
# =========================================================
@bot.event
async def on_message(message):
    if not message.text:
        return

    text = message.text.strip()
    user_id = message.author.id

    # =====================================================
    # Commands & Menu Triggers
    # =====================================================
    if text == "/start":
        state_manager.clear_state(user_id)
        await safe_delete_previous_inline(message, user_id)
        await handle_start(message)
        return

    if text in ("/register", "📝 ثبت اطلاعات"):
        await safe_delete_previous_inline(message, user_id)
        await handle_patient_registration(message)
        return

    if text == "/patient":
        await safe_delete_previous_inline(message, user_id)
        await handle_patient_lookup(message)
        return

    if text == "/appointments":
        await safe_delete_previous_inline(message, user_id)
        await handle_my_appointments(message)
        return

    if text == "/cancel":
        await safe_delete_previous_inline(message, user_id)
        await handle_cancel_appointment(message)
        return

    if text == "/book":
        await safe_delete_previous_inline(message, user_id)
        await handle_booking_start(message)
        return

    # =====================================================
    # Main Menu
    # =====================================================
    if text == "📅 دریافت نوبت":
        await safe_delete_previous_inline(message, user_id)
        await handle_booking_start(message)
        return

    if text == "📋 نوبت‌های من":
        await safe_delete_previous_inline(message, user_id)
        await handle_my_appointments(message)
        return

    if text == "👤 اطلاعات بیمار":
        await safe_delete_previous_inline(message, user_id)
        await handle_patient_lookup(message)
        return

    if text == "🏥 اطلاعات درمانگاه":
        await safe_delete_previous_inline(message, user_id)
        await handle_clinic_info(message)
        return

    # =====================================================
    # Patient Submenu
    # =====================================================
    if text in ("✏️ ویرایش اطلاعات بیمار", "ویرایش اطلاعات"):
        await safe_delete_previous_inline(message, user_id)
        await handle_patient_edit(message)
        return

    if text in ("↩️ بازگشت به منوی اصلی", "لغو"):
        state_manager.clear_state(user_id)
        await safe_delete_previous_inline(message, user_id)
        await send_welcome_message(message, user_id)
        return

    # =====================================================
    # Admin
    # =====================================================
    if text == "/admin":
        await handle_admin_panel(message)
        return

    if text == "/pending":
        await handle_pending_appointments(message)
        return

    if text == "/schedule":
        await handle_manage_schedule(message)
        return

    if text == "/patients":
        await handle_manage_patients(message)
        return

    # =====================================================
    # State Handling
    # =====================================================
    state = state_manager.get_state(user_id)
    if state is None:
        return

    # -----------------------------------------------------
    # Booking
    # -----------------------------------------------------
    handled = await process_booking_message(message)
    if handled:
        return

    # -----------------------------------------------------
    # Cancel Appointment
    # -----------------------------------------------------
    handled = await process_cancel_appointment(message)
    if handled:
        return

    # -----------------------------------------------------
    # Patient Registration / Edit
    # -----------------------------------------------------
    handled = await process_registration_message(message)
    if handled:
        return

# =========================================================
# Callback
# =========================================================
@bot.event
async def on_callback(query):
    await handle_callback(query)

# =========================================================
# Run
# =========================================================
def main():
    logger.info("Starting ClinicBot...")
    bot.run()

if __name__ == "__main__":
    main()