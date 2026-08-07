import asyncio
from datetime import datetime, timedelta
from bale import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.repository import repository
from api.crud import get_schedule_config
from utils.helpers import to_persian_date, to_date_label, get_service_display_name, get_msg_id, activate_text_keyboard
from utils.keyboards import (
    booking_target_keyboard, booking_checkout_keyboard, booking_confirmation_keyboard, back_to_services_keyboard,
    other_cancel_inline_keyboard, other_back_inline_keyboard, gender_keyboard, insurance_keyboard, main_keyboard,
    other_patient_confirm_keyboard, edit_other_cancel_inline_keyboard, edit_other_back_inline_keyboard
)
from utils.state_manager import state_manager
from utils.validators import validate_full_name, validate_national_id, validate_phone_number, normalize_digits
from handlers.patients import REGISTRATION_NATIONAL_ID, send_tracked_message

BOOKING_TARGET = "booking_target"
BOOKING_SERVICE = "booking_service"
BOOKING_DATE = "booking_date"
BOOKING_TIME = "booking_time"
BOOKING_CHECKOUT = "booking_checkout"

OTHER_PATIENT_NATIONAL_ID = "booking_other_national_id"
OTHER_PATIENT_NAME = "booking_other_name"
OTHER_PATIENT_PHONE = "booking_other_phone"
OTHER_PATIENT_GENDER = "booking_other_gender"
OTHER_PATIENT_INSURANCE = "booking_other_insurance"

EDIT_OTHER_NAME = "edit_other_name"
EDIT_OTHER_PHONE = "edit_other_phone"
EDIT_OTHER_GENDER = "edit_other_gender"
EDIT_OTHER_INSURANCE = "edit_other_insurance"

GENDER_MAP = {"آقا": "male", "خانم": "female"}
INSURANCE_MAP = {"سلامت": "health", "تأمین اجتماعی": "social_security", "تامین اجتماعی": "social_security", "نیروهای مسلح": "armed_forces", "بدون بیمه": "none"}
GENDER_DISPLAY = {"male": "آقا", "female": "خانم"}
INSURANCE_DISPLAY = {"health": "سلامت", "social_security": "تأمین اجتماعی", "armed_forces": "نیروهای مسلح", "none": "بدون بیمه"}

# --- Custom Keyboards designed specifically for beautiful flow ---
def get_persian_weekday(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = {
            5: "شنبه",
            6: "یک‌شنبه",
            0: "دوشنبه",
            1: "سه‌شنبه",
            2: "چهارشنبه",
            3: "پنج‌شنبه",
            4: "جمعه"
        }
        return weekdays[dt.weekday()]
    except Exception:
        return ""

def custom_booking_services_keyboard(services):
    kb = InlineKeyboardMarkup()
    row_idx = 1
    for i, s in enumerate(services):
        row_idx = (i // 2) + 1
        kb.add(InlineKeyboardButton(text=s["name"], callback_data=f"booking_service:{s['id']}"), row_idx)
    kb.add(InlineKeyboardButton(text="بازگشت", callback_data="booking_back:target"), row_idx + 1)
    return kb

def custom_booking_dates_keyboard(dates, availability):
    kb = InlineKeyboardMarkup()
    for i, d in enumerate(dates):
        row_idx = i + 1  # قرار دادن دکمه‌های تاریخ به صورت تکی در هر ردیف
        status = availability.get(d, "disabled")
        weekday = get_persian_weekday(d)
        p_date = to_persian_date(d)
        
        base_text = f"📅 {weekday} - {p_date}"
        
        if status == "available":
            text = base_text
            cb = f"booking_date:{d}"
        elif status == "full":
            text = f"{base_text} (تکمیل)"
            cb = f"booking_date:full:{d}"
        else:
            text = f"{base_text} (غیرفعال)"
            cb = f"booking_date:disabled:{d}"
            
        kb.add(InlineKeyboardButton(text=text, callback_data=cb), row_idx)
        
    kb.add(InlineKeyboardButton(text="بازگشت", callback_data="booking_back:services"), len(dates) + 1)
    return kb

def custom_booking_times_keyboard(times, appointment_date):
    kb = InlineKeyboardMarkup()
    row_idx = 1
    for i, t in enumerate(times):
        row_idx = (i // 2) + 1
        is_full = int(t.get("booked_count", 0)) >= int(t.get("capacity", 1))
        text = f"{t['start_time']} (تکمیل)" if is_full else t['start_time']
        cb = f"booking_time:full:{appointment_date}:{t['start_time']}" if is_full else f"booking_time:{appointment_date}:{t['start_time']}"
        kb.add(InlineKeyboardButton(text=text, callback_data=cb), row_idx)
    kb.add(InlineKeyboardButton(text="بازگشت", callback_data="booking_back:dates"), row_idx + 1)
    return kb
# ------------------------------------------------------------------

def get_selected_patient(user_id: int):
    user = repository.get_user_by_bale_id(user_id)
    if user is None: return None, None
    patient = repository.get_patient_by_user_id(user["id"])
    return user, patient

def get_services_for_booking():
    services = repository.get_services()
    return [s for s in services if s.get("is_active", 1) == 1]

async def safe_delete_previous_inline(message, user_id: int):
    last_id = state_manager.get_data(user_id, "last_prompt_id")
    if last_id:
        try:
            bot = message.get_bot() if hasattr(message, "get_bot") else None
            if bot:
                await bot.edit_message(message.chat_id, last_id, text=state_manager.get_data(user_id, "last_prompt_text", " "), components=None)
        except:
            pass
        state_manager.set_data(user_id, "last_prompt_id", None)

async def send_callback_message(query: CallbackQuery, text: str, components=None, delete_message=True):
    if not query.message: return
    bot = query.message.get_bot()
    chat_id = query.message.chat_id
    if delete_message:
        try: await query.message.edit(text, components=components)
        except Exception:
            try: await query.message.delete()
            except: pass
            msg = await bot.send_message(chat_id, text, components=components)
            msg_id = get_msg_id(msg)
            if msg_id: 
                state_manager.set_data(query.user.id, "last_prompt_id", msg_id)
                state_manager.set_data(query.user.id, "last_prompt_text", text)

async def show_services(target, user_id: int):
    services = get_services_for_booking()
    if not services:
        text = "در حال حاضر خدمات نوبت‌دهی در سیستم ثبت نشده است."
        if isinstance(target, CallbackQuery):
            from utils.keyboards import main_keyboard
            await send_callback_message(target, text, components=main_keyboard())
        else:
            from utils.keyboards import main_keyboard
            await target.reply(text, components=main_keyboard())
        return

    state_manager.set_state(user_id, BOOKING_SERVICE)
    state_manager.set_data(user_id, "services", services)

    text = "🗓 دریافت نوبت\n\nلطفاً خدمت مورد نظر خود را انتخاب کنید:"
    keyboard = custom_booking_services_keyboard(services)

    if isinstance(target, CallbackQuery): await send_callback_message(target, text, components=keyboard)
    else: await target.reply(text, components=keyboard)

async def show_other_patient_profile(target, user_id: int, patient: dict):
    text = (
        "🪪 **پرونده بیمار یافت شد:**\n\n"
        f"👤 نام: {patient.get('first_name','')} {patient.get('last_name','')}\n"
        f"💳 کد ملی: {patient.get('national_id','')}\n"
        f"📱 تلفن: {patient.get('phone_number','')}\n"
        f"⚧ جنسیت: {GENDER_DISPLAY.get(patient.get('gender', 'male'), 'نامشخص')}\n"
        f"🏥 بیمه: {INSURANCE_DISPLAY.get(patient.get('insurance', 'none'), 'نامشخص')}\n\n"
        "لطفاً از گزینه‌های زیر استفاده کنید 👇"
    )
    state_manager.set_state(user_id, "BOOKING_OTHER_CONFIRM")
    if isinstance(target, CallbackQuery):
        await send_callback_message(target, text, components=other_patient_confirm_keyboard())
    else:
        await send_tracked_message(target, user_id, text, components=other_patient_confirm_keyboard())

async def handle_booking_other_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_other:"): return
    action = data.split(":", 1)[1]
    
    if action == "proceed":
        await show_services(query, user_id)
    elif action == "edit":
        state_manager.set_state(user_id, EDIT_OTHER_NAME)
        bot = query.message.get_bot()
        chat_id = query.message.chat_id
        await activate_text_keyboard(bot, chat_id, is_registered=True)
        text = "✏️ **ویرایش اطلاعات**\n\n👤 لطفاً نام و نام خانوادگی جدید را وارد کنید:\n\n(مثال: علی رضایی)"
        await send_callback_message(query, text, components=edit_other_cancel_inline_keyboard())
    elif action == "cancel_edit":
        national_id = state_manager.get_data(user_id, "other_national_id")
        patient = repository.get_patient_by_national_id(national_id)
        if patient:
            await show_other_patient_profile(query, user_id, patient)

async def handle_booking_start(message: Message):
    user_id = message.author.id
    user = repository.get_user_by_bale_id(user_id)
    if user is None:
        await message.reply("اطلاعات کاربری شما پیدا نشد.\nلطفاً ابتدا /start را بزنید.")
        return
    state_manager.clear_state(user_id)
    state_manager.set_state(user_id, BOOKING_TARGET)
    await send_tracked_message(message, user_id, "🗓 دریافت نوبت\n\nلطفاً مشخص کنید نوبت را برای چه کسی می‌خواهید:", components=booking_target_keyboard())

async def handle_booking_start_callback(query: CallbackQuery):
    user_id = query.user.id
    state_manager.clear_state(user_id)
    state_manager.set_state(user_id, BOOKING_TARGET)
    await send_callback_message(query, "🗓 دریافت نوبت\n\nلطفاً مشخص کنید نوبت را برای چه کسی می‌خواهید:", components=booking_target_keyboard())

async def handle_booking_target_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_target:") or state_manager.get_state(user_id) != BOOKING_TARGET: return
    target = data.split(":", 1)[1]

    if target == "self":
        user, patient = get_selected_patient(user_id)
        if user is None or patient is None or not patient.get("national_id"):
            state_manager.clear_state(user_id)
            state_manager.set_state(user_id, REGISTRATION_NATIONAL_ID)
            from utils.keyboards import cancel_only_inline_keyboard
            bot = query.message.get_bot()
            await activate_text_keyboard(bot, query.message.chat_id, is_registered=False)
            await send_callback_message(query, "👤 برای دریافت نوبت، ابتدا باید اطلاعات شما ثبت شود.\n\nلطفاً کد ملی ۱۰ رقمی خود را وارد کنید:\n\n(مثال: 0012345678)", components=cancel_only_inline_keyboard("❌ لغو"))
            return
        state_manager.set_data(user_id, "booking_target", "self")
        state_manager.set_data(user_id, "booking_patient_id", patient["id"])
        state_manager.set_data(user_id, "patient_full_name", f"{patient.get('first_name','')} {patient.get('last_name','')}")
        await show_services(query, user_id)
        return

    if target == "other":
        state_manager.clear_state(user_id)
        state_manager.set_data(user_id, "booking_target", "other")
        state_manager.set_state(user_id, OTHER_PATIENT_NATIONAL_ID)
        bot = query.message.get_bot()
        chat_id = query.message.chat_id
        await activate_text_keyboard(bot, chat_id, is_registered=True)
        text = "👥 ثبت نوبت برای شخص دیگر\n\nابتدا لطفاً کد ملی ۱۰ رقمی فرد موردنظر را وارد کنید:\n\n(مثال: 0012345678)"
        await send_callback_message(query, text, components=other_cancel_inline_keyboard())

async def handle_booking_service_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_service:") or state_manager.get_state(user_id) != BOOKING_SERVICE: return
    
    if data == "booking_service:inactive":
        await query.message.get_bot().send_message(query.message.chat_id, "⚠️ این خدمت در حال حاضر غیرفعال است.")
        return
        
    try: service_id = int(data.split(":", 1)[1])
    except: return

    services = repository.get_services()
    service = next((s for s in services if s["id"] == service_id), None)
    
    if service is None:
        await send_callback_message(query, "خدمت انتخاب‌شده معتبر نیست.", components=custom_booking_services_keyboard(get_services_for_booking()))
        return

    state_manager.set_data(user_id, "service_id", service_id)
    state_manager.set_data(user_id, "service_name_base", service["name"])
    target = state_manager.get_data(user_id, "booking_target")

    if bool(service.get("has_gender", 0)):
        if target == "self":
            _, patient = get_selected_patient(user_id)
            gender = patient.get("gender") if patient else "male"
        else:
            gender = state_manager.get_data(user_id, "other_gender", "male")
    else:
        gender = "all"

    state_manager.set_data(user_id, "gender", gender)
    await show_booking_dates(query, user_id)

async def show_booking_dates(query: CallbackQuery, user_id: int):
    service_id = state_manager.get_data(user_id, "service_id")
    gender = state_manager.get_data(user_id, "gender")
    base_name = state_manager.get_data(user_id, "service_name_base", "خدمت")
    
    services = repository.get_services()
    service_obj = next((s for s in services if s["id"] == service_id), None)
    if service_obj and bool(service_obj.get("has_gender", 0)):
        service_name = f"{base_name} {'آقایان' if gender == 'male' else 'بانوان'}"
    else:
        service_name = base_name

    if service_id is None or gender not in ("male", "female", "all"):
        from utils.keyboards import main_keyboard
        await send_callback_message(query, "اطلاعات رزرو ناقص است.\nلطفاً دوباره دریافت نوبت را شروع کنید.", components=main_keyboard())
        state_manager.clear_state(user_id)
        return

    from api.crud import get_schedule_config
    from database.connection import fetch_all
    config = get_schedule_config()
    days_ahead = int(config.get("booking_days_ahead", 7))
    working_days = config.get("working_days", [])
    
    today = datetime.now()
    dates = []
    valid_found = 0
    offset = 0
    
    while valid_found < days_ahead and offset < 60:
        curr = today + timedelta(days=offset)
        if int(curr.weekday()) in working_days:
            dates.append(curr.strftime("%Y-%m-%d"))
            valid_found += 1
        offset += 1
    
    availability = {}
    for d in dates:
        times = repository.get_available_times(service_id=service_id, appointment_date=d, gender=gender)
        if not times:
            availability[d] = "disabled"
        else:
            has_avail = any(int(item.get("booked_count", 0)) < int(item.get("capacity", 1)) for item in times)
            availability[d] = "available" if has_avail else "full"

    state_manager.set_data(user_id, "dates", dates)
    state_manager.set_state(user_id, BOOKING_DATE)
    
    if not dates:
        await send_callback_message(query, f"🏥 خدمت انتخاب شده: {service_name}\n\nمتأسفانه در حال حاضر هیچ ظرفیتی برای این خدمت در روزهای آینده تعریف نشده است.", components=back_to_services_keyboard())
        return
        
    await send_callback_message(query, f"🏥 خدمت انتخاب شده: {service_name}\n\nلطفاً تاریخ موردنظر را انتخاب کنید:\n\n❌ تاریخ‌های تکمیل‌شده با علامت (تکمیل) مشخص شده‌اند.", components=custom_booking_dates_keyboard(dates, availability))

async def handle_booking_date_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_date:") or state_manager.get_state(user_id) != BOOKING_DATE: return
    
    if data.startswith("booking_date:full:"):
        await query.message.get_bot().send_message(query.message.chat_id, "⚠️ ظرفیت این روز تکمیل شده است.")
        return
        
    if data.startswith("booking_date:disabled:"):
        await query.message.get_bot().send_message(query.message.chat_id, "⚠️ در این تاریخ هیچ نوبتی برای این خدمت تعریف نشده است.")
        return
        
    appointment_date = data.split(":", 1)[1]
    dates = state_manager.get_data(user_id, "dates", [])

    if appointment_date not in dates: return
    service_id = state_manager.get_data(user_id, "service_id")
    gender = state_manager.get_data(user_id, "gender")

    times = repository.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
    has_available_time = any(int(item.get("booked_count", 0)) < int(item.get("capacity", 1)) for item in times)

    if not has_available_time:
        await show_booking_dates(query, user_id)
        return

    state_manager.set_data(user_id, "appointment_date", appointment_date)
    state_manager.set_data(user_id, "times", times)
    state_manager.set_state(user_id, BOOKING_TIME)

    base_name = state_manager.get_data(user_id, "service_name_base", "خدمت")
    services = repository.get_services()
    service_obj = next((s for s in services if s["id"] == service_id), None)
    if service_obj and bool(service_obj.get("has_gender", 0)):
        service_name = f"{base_name} {'آقایان' if gender == 'male' else 'بانوان'}"
    else:
        service_name = base_name

    await send_callback_message(query, f"🏥 خدمت: {service_name}\n📅 تاریخ: {to_persian_date(appointment_date)}\n\nلطفاً ساعت موردنظر را انتخاب کنید:", components=custom_booking_times_keyboard(times, appointment_date))

async def handle_booking_time_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_time:") or state_manager.get_state(user_id) != BOOKING_TIME: return
    
    if data.startswith("booking_time:full:"):
        await query.message.get_bot().send_message(query.message.chat_id, "⚠️ این ساعت پر شده است.")
        return
        
    parts = data.split(":", 2)
    if len(parts) != 3: return
    appointment_date, start_time = parts[1], parts[2]

    service_id = state_manager.get_data(user_id, "service_id")
    gender = state_manager.get_data(user_id, "gender")

    times = repository.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
    slot = next((t for t in times if t["start_time"] == start_time), None)
    
    if not slot or int(slot.get("booked_count", 0)) >= int(slot.get("capacity", 1)):
        await send_callback_message(query, "⚠️ این ظرفیت همین الان پر شد.\n\nلطفاً ساعت دیگری انتخاب کنید.", components=custom_booking_times_keyboard(times, appointment_date))
        return

    value = repository.get_setting("appointment_duration")
    try:
        duration = int(value or "30")
        end_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")
    except ValueError:
        return

    state_manager.set_data(user_id, "start_time", start_time)
    state_manager.set_data(user_id, "end_time", end_time)
    state_manager.set_state(user_id, BOOKING_CHECKOUT)

    base_name = state_manager.get_data(user_id, "service_name_base")
    services = repository.get_services()
    service_obj = next((s for s in services if s["id"] == service_id), None)
    if service_obj and bool(service_obj.get("has_gender", 0)):
        service_name = f"{base_name} {'آقایان' if gender == 'male' else 'بانوان'}"
    else:
        service_name = base_name

    patient_name = state_manager.get_data(user_id, "patient_full_name", "بیمار")
    gender_text = "آقا" if gender == "male" else ("خانم" if gender == "female" else "عمومی")

    summary_text = (
        "📋 پیش‌فاکتور و تأیید نهایی نوبت\n\n"
        f"👤 بیمار: {patient_name}\n"
        f"🏥 خدمت: {service_name}\n"
        f"⚧ جنسیت: {gender_text}\n"
        f"📅 تاریخ: {to_date_label(appointment_date)}\n"
        f"🕘 ساعت: {start_time}\n\n"
        "در صورت صحت اطلاعات، روی «✅ تأیید و ثبت نهایی» کلیک کنید."
    )
    await send_callback_message(query, summary_text, components=booking_checkout_keyboard())

async def handle_booking_checkout_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_checkout:") or state_manager.get_state(user_id) != BOOKING_CHECKOUT: return
    action = data.split(":", 1)[1]

    if action == "cancel":
        state_manager.clear_state(user_id)
        try: await query.message.delete()
        except: pass
        from utils.helpers import send_welcome_message
        await send_welcome_message(query, user_id)
        return

    if action == "confirm":
        data_cache = state_manager.get_all_data(user_id)
        service_id = data_cache.get("service_id")
        gender = data_cache.get("gender")
        appointment_date = data_cache.get("appointment_date")
        start_time = data_cache.get("start_time")
        end_time = data_cache.get("end_time")
        target = data_cache.get("booking_target")
        
        base_name = data_cache.get("service_name_base")
        services = repository.get_services()
        service_obj = next((s for s in services if s["id"] == service_id), None)
        if service_obj and bool(service_obj.get("has_gender", 0)):
            service_name = f"{base_name} {'آقایان' if gender == 'male' else 'بانوان'}"
        else:
            service_name = base_name

        times = repository.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
        slot = next((t for t in times if t["start_time"] == start_time), None)
        
        if not slot or int(slot.get("booked_count", 0)) >= int(slot.get("capacity", 1)):
            state_manager.set_state(user_id, BOOKING_TIME)
            await send_callback_message(query, "⚠️ متاسفانه در همین چند لحظه ظرفیت این ساعت پر شد.\nلطفاً ساعت دیگری انتخاب کنید.", components=custom_booking_times_keyboard(times, appointment_date))
            return

        user, patient = get_selected_patient(user_id)

        if target == "other":
            if data_cache.get("other_patient_exists"):
                patient_id = data_cache.get("booking_patient_id")
                try: repository.add_patient_profile(user["id"], patient_id)
                except: pass
            else:
                try:
                    patient_id = repository.create_patient(
                        user_id=user["id"],
                        national_id=data_cache["other_national_id"], first_name=data_cache["other_first_name"],
                        last_name=data_cache["other_last_name"], phone_number=data_cache["other_phone"], birth_date=None,
                        gender=data_cache["other_gender"], insurance=data_cache["other_insurance"]
                    )
                    repository.add_patient_profile(user["id"], patient_id)
                except Exception:
                    try: await query.message.delete()
                    except: pass
                    await query.message.get_bot().send_message(query.message.chat_id, "❌ خطا در ذخیره اطلاعات. لطفاً مجدداً تلاش کنید.")
                    state_manager.clear_state(user_id)
                    return
        else:
            if not patient: 
                try: await query.message.delete()
                except: pass
                await query.message.get_bot().send_message(query.message.chat_id, "❌ خطای دسترسی به اطلاعات شما.")
                state_manager.clear_state(user_id)
                return
            patient_id = patient["id"]

        try:
            appointment_gender = gender if gender != "all" else (patient.get("gender") if patient else "male")
            appointment_id = repository.create_appointment_if_available(
                patient_id=patient_id, service_id=service_id, appointment_date=appointment_date,
                start_time=start_time, end_time=end_time, gender=appointment_gender, status="scheduled", created_by=(user["id"] if user else None)
            )
        except ValueError as e:
            if str(e) == "active_appointment_exists":
                error_msg = (
                    "❌ **شخصی با این کد ملی در حال حاضر یک نوبت فعال برای این خدمت دارد.**\n"
                    "تا زمانی که نوبت قبلی انجام یا لغو نشود، نمی‌توانید نوبت جدیدی برای همین خدمت دریافت کنید.\n\n"
                    "🔸 **راهنما:**\n"
                    "• جهت مشاهده جزئیات نوبت و یا لغو آن، لطفاً از منوی **«📋 نوبت‌های من»** اقدام کنید.\n"
                    "• در صورتی که قصد دارید برای شخص دیگری (بجز خودتان) نوبت بگیرید، از منوی دریافت نوبت گزینه **«👥 برای شخص دیگر»** را انتخاب نمایید."
                )
                await send_callback_message(query, error_msg, components=back_to_services_keyboard())
                return
            else:
                try: await query.message.delete()
                except: pass
                await query.message.get_bot().send_message(query.message.chat_id, "❌ خطا در ثبت نوبت. لطفاً دوباره تلاش کنید.")
                state_manager.clear_state(user_id)
                return
        except Exception:
            try: await query.message.delete()
            except: pass
            await query.message.get_bot().send_message(query.message.chat_id, "❌ خطا در ثبت نوبت. لطفاً دوباره تلاش کنید.")
            state_manager.clear_state(user_id)
            return

        if appointment_id is None:
            state_manager.set_state(user_id, BOOKING_TIME)
            times = repository.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
            await send_callback_message(query, "⚠️ متاسفانه در همین لحظه ظرفیت این ساعت پر شد.\nلطفاً ساعت دیگری انتخاب کنید.", components=custom_booking_times_keyboard(times, appointment_date))
            return

        state_manager.clear_state(user_id)
        
        success_msg = (
            f"✅ نوبت با موفقیت ثبت نهایی شد.\n\n"
            f"🏥 خدمت: {service_name}\n"
            f"📅 تاریخ: {to_persian_date(appointment_date)}\n"
            f"🕘 ساعت: {start_time}\n"
            f"🔖 کد پیگیری: CF-{appointment_id:06d}\n\n\n"
            f"🔹 جهت مشاهده جزئیات نوبت و یا لغو آن، از منوی «📋 نوبت‌های من» اقدام کنید.\n\n"
            f"🔹 امکان لغو نوبت تنها تا ۲۴ ساعت قبل* از زمان رزرو وجود دارد."
        )
        await send_callback_message(query, success_msg, components=booking_confirmation_keyboard())

async def handle_booking_back_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_back:"): return
    destination = data.split(":", 1)[1]

    if destination == "home":
        state_manager.clear_state(user_id)
        try: await query.message.delete()
        except: pass
        from utils.helpers import send_welcome_message
        await send_welcome_message(query, user_id)
        return
    if destination == "target":
        state_manager.clear_state(user_id)
        state_manager.set_state(user_id, BOOKING_TARGET)
        await send_callback_message(query, "🗓 دریافت نوبت\n\nنوبت را برای چه کسی می‌خواهید؟", components=booking_target_keyboard())
        return
    if destination == "services":
        await show_services(query, user_id)
        return
    if destination == "dates":
        service_id = state_manager.get_data(user_id, "service_id")
        gender = state_manager.get_data(user_id, "gender")
        dates = state_manager.get_data(user_id, "dates", [])
        state_manager.set_state(user_id, BOOKING_DATE)
        
        availability = {}
        for d in dates:
            times = repository.get_available_times(service_id=service_id, appointment_date=d, gender=gender)
            if not times:
                availability[d] = "disabled"
            else:
                has_avail = any(int(item.get("booked_count", 0)) < int(item.get("capacity", 1)) for item in times)
                availability[d] = "available" if has_avail else "full"
            
        await send_callback_message(query, "🗓 لطفاً تاریخ موردنظر را انتخاب کنید:\n\n❌ تاریخ‌های تکمیل‌شده با علامت (تکمیل) مشخص شده‌اند.", components=custom_booking_dates_keyboard(dates, availability))
        return

async def process_booking_message(message: Message) -> bool:
    user_id = message.author.id
    state = state_manager.get_state(user_id)
    if state is None: return False
    value = (message.text or "").strip()

    if not value: return True

    if state == OTHER_PATIENT_NATIONAL_ID:
        if not validate_national_id(value):
            await send_tracked_message(message, user_id, "کد ملی نامعتبر است. لطفاً دقیقاً ۱۰ رقم وارد کنید.", components=other_back_inline_keyboard())
            return True

        value = normalize_digits(value)
        await safe_delete_previous_inline(message, user_id)

        user, patient = get_selected_patient(user_id)
        if patient and patient.get("national_id") == value:
            from utils.keyboards import booking_target_keyboard
            state_manager.clear_state(user_id)
            state_manager.set_state(user_id, BOOKING_TARGET)
            await send_tracked_message(message, user_id, "⚠️ این کد ملی متعلق به حساب کاربری خود شماست.\n\nبرای دریافت نوبت برای خودتان، لطفاً از گزینه «👤 برای خودم» استفاده کنید:", components=booking_target_keyboard())
            return True

        existing_patient = repository.get_patient_by_national_id(value)

        if existing_patient:
            state_manager.set_data(user_id, "other_national_id", value)
            state_manager.set_data(user_id, "other_patient_exists", True)
            state_manager.set_data(user_id, "booking_patient_id", existing_patient["id"])
            state_manager.set_data(user_id, "other_gender", existing_patient.get("gender", "male"))
            state_manager.set_data(user_id, "patient_full_name", f"{existing_patient.get('first_name','')} {existing_patient.get('last_name','')}")

            await show_other_patient_profile(message, user_id, existing_patient)
        else:
            state_manager.set_data(user_id, "other_national_id", value)
            state_manager.set_data(user_id, "other_patient_exists", False)
            state_manager.set_state(user_id, OTHER_PATIENT_NAME)
            await send_tracked_message(message, user_id, "👤 این کد ملی در سیستم ثبت نشده است.\n\nلطفاً نام و نام خانوادگی بیمار را وارد کنید:\n\n(مثال: علی رضایی)", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_NAME:
        normalized = " ".join(value.split())
        if not validate_full_name(normalized):
            await send_tracked_message(message, user_id, "نام معتبر نیست.\n\n(مثال: علی رضایی)", components=other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        parts = normalized.split()
        state_manager.set_data(user_id, "other_first_name", parts[0])
        state_manager.set_data(user_id, "other_last_name", " ".join(parts[1:]))
        state_manager.set_data(user_id, "patient_full_name", normalized)
        
        state_manager.set_state(user_id, OTHER_PATIENT_PHONE)
        await send_tracked_message(message, user_id, "📱 لطفاً شماره موبایل را وارد کنید:\n\n(مثال: 09123456789)", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_PHONE:
        if not validate_phone_number(value):
            await send_tracked_message(message, user_id, "❌ شماره موبایل نامعتبر است. حتماً باید ۱۱ رقم باشد و با 09 شروع شود. مجدداً ارسال کنید:", components=other_back_inline_keyboard())
            return True
            
        value = normalize_digits(value)
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "other_phone", value)
        state_manager.set_state(user_id, OTHER_PATIENT_GENDER)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
        await send_tracked_message(message, user_id, "⚧ لطفاً جنسیت را انتخاب کنید:", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_GENDER:
        if value not in GENDER_MAP:
            await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
            await send_tracked_message(message, user_id, "لطفاً منحصراً از دکمه‌های پایین صفحه استفاده کنید.", components=other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        
        state_manager.set_data(user_id, "other_gender", GENDER_MAP[value])
        state_manager.set_state(user_id, OTHER_PATIENT_INSURANCE)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=insurance_keyboard())
        await send_tracked_message(message, user_id, "🏥 لطفاً بیمه را انتخاب کنید:", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_INSURANCE:
        if value not in INSURANCE_MAP:
            await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=insurance_keyboard())
            await send_tracked_message(message, user_id, "لطفاً منحصراً از دکمه‌های پایین صفحه استفاده کنید.", components=other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        
        state_manager.set_data(user_id, "other_insurance", INSURANCE_MAP[value])
        
        await message.reply("✅ اطلاعات فرد دریافت شد. در حال انتقال به بخش انتخاب خدمات...", components=main_keyboard())
        await asyncio.sleep(0.5)
        await show_services(message, user_id)
        return True

    if state == EDIT_OTHER_NAME:
        normalized = " ".join(value.split())
        if not validate_full_name(normalized):
            await send_tracked_message(message, user_id, "نام معتبر نیست.\n\n(مثال: علی رضایی)", components=edit_other_cancel_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        parts = normalized.split()
        state_manager.set_data(user_id, "edit_other_first_name", parts[0])
        state_manager.set_data(user_id, "edit_other_last_name", " ".join(parts[1:]))
        state_manager.set_state(user_id, EDIT_OTHER_PHONE)
        await send_tracked_message(message, user_id, "📱 لطفاً شماره موبایل جدید را وارد کنید:\n\n(مثال: 09123456789)", components=edit_other_back_inline_keyboard())
        return True

    if state == EDIT_OTHER_PHONE:
        if not validate_phone_number(value):
            await send_tracked_message(message, user_id, "شماره موبایل نامعتبر است.", components=edit_other_back_inline_keyboard())
            return True
            
        value = normalize_digits(value)
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_other_phone", value)
        state_manager.set_state(user_id, EDIT_OTHER_GENDER)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
        await send_tracked_message(message, user_id, "⚧ لطفاً جنسیت جدید را انتخاب کنید:", components=edit_other_back_inline_keyboard())
        return True

    if state == EDIT_OTHER_GENDER:
        if value not in GENDER_MAP:
            await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
            await send_tracked_message(message, user_id, "لطفاً منحصراً از دکمه‌های پایین صفحه استفاده کنید.", components=edit_other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        
        state_manager.set_data(user_id, "edit_other_gender", GENDER_MAP[value])
        state_manager.set_state(user_id, EDIT_OTHER_INSURANCE)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=insurance_keyboard())
        await send_tracked_message(message, user_id, "🏥 لطفاً بیمه جدید را انتخاب کنید:", components=edit_other_back_inline_keyboard())
        return True

    if state == EDIT_OTHER_INSURANCE:
        if value not in INSURANCE_MAP:
            await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=insurance_keyboard())
            await send_tracked_message(message, user_id, "لطفاً منحصراً از دکمه‌های پایین صفحه استفاده کنید.", components=edit_other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_other_insurance", INSURANCE_MAP[value])
        
        data_cache = state_manager.get_all_data(user_id)
        patient_id = data_cache.get("booking_patient_id")
        national_id = data_cache.get("other_national_id")

        try:
            try:
                repository.update_patient(
                    patient_id=patient_id, first_name=data_cache["edit_other_first_name"], last_name=data_cache["edit_other_last_name"],
                    phone_number=data_cache["edit_other_phone"], birth_date=None,
                    gender=data_cache["edit_other_gender"], insurance=data_cache["edit_other_insurance"], national_id=national_id
                )
            except TypeError:
                repository.update_patient(
                    patient_id=patient_id, first_name=data_cache["edit_other_first_name"], last_name=data_cache["edit_other_last_name"],
                    phone_number=data_cache["edit_other_phone"], birth_date=None,
                    gender=data_cache["edit_other_gender"], insurance=data_cache["edit_other_insurance"]
                )
        except Exception:
            await message.reply("❌ خطا در ثبت اطلاعات.")
            return True

        state_manager.set_data(user_id, "other_gender", data_cache["edit_other_gender"])
        state_manager.set_data(user_id, "patient_full_name", f"{data_cache['edit_other_first_name']} {data_cache['edit_other_last_name']}")
        
        await message.reply("✅ اطلاعات شخص با موفقیت ویرایش شد.", components=main_keyboard())
        await asyncio.sleep(0.5)
        
        updated_patient = repository.get_patient_by_national_id(national_id)
        await show_other_patient_profile(message, user_id, updated_patient)
        return True

    if state in (BOOKING_SERVICE, BOOKING_DATE, BOOKING_TIME, BOOKING_CHECKOUT):
        await message.reply("لطفاً از طریق دکمه‌های شیشه‌ای نمایش‌داده‌شده در بالا انتخاب خود را انجام دهید.")
        return True

    return False