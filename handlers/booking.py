import asyncio
from datetime import datetime, timedelta
from bale import Message, CallbackQuery

from database.repository import repository
from services.schedule_service import schedule_service
from utils.helpers import to_persian_date, to_date_label, get_service_display_name, get_msg_id, activate_text_keyboard
from utils.keyboards import (
    booking_target_keyboard, booking_services_keyboard, booking_dates_keyboard, booking_times_keyboard,
    booking_checkout_keyboard, booking_confirmation_keyboard, back_to_services_keyboard,
    other_cancel_inline_keyboard, other_back_inline_keyboard, gender_keyboard, insurance_keyboard, main_keyboard
)
from utils.state_manager import state_manager
from utils.validators import validate_full_name, validate_national_id, validate_phone_number
from handlers.patients import REGISTRATION_NAME, safe_delete_previous_inline, send_tracked_message

BOOKING_TARGET = "booking_target"
BOOKING_SERVICE = "booking_service"
BOOKING_DATE = "booking_date"
BOOKING_TIME = "booking_time"
BOOKING_CHECKOUT = "booking_checkout"

OTHER_PATIENT_NAME = "booking_other_name"
OTHER_PATIENT_NATIONAL_ID = "booking_other_national_id"
OTHER_PATIENT_PHONE = "booking_other_phone"
OTHER_PATIENT_GENDER = "booking_other_gender"
OTHER_PATIENT_INSURANCE = "booking_other_insurance"

SERVICE_DEFINITIONS = {
    "ویزیت دکتر گرایلی": False,
    "غمز و رگ گیری": False,
    "طب سوزنی": False,
    "فصد": False,
    "اسکن کل بدن": False,
    "سم زدایی": False,
    "امبدینگ(لاغری)": False,
    "بادکش": True,
    "حجامت عام": True,
    "زالودرمانی": True,
}

GENDER_MAP = {"آقا": "male", "خانم": "female"}
INSURANCE_MAP = {"سلامت": "health", "تأمین اجتماعی": "social_security", "نیروهای مسلح": "armed_forces", "بدون بیمه": "none"}

def get_selected_patient(user_id: int):
    user = repository.get_user_by_bale_id(user_id)
    if user is None: return None, None
    patient = repository.get_patient_by_user_id(user["id"])
    return user, patient

def get_service_record(service_id: int):
    try: service_id = int(service_id)
    except: return None
    services = repository.get_services()
    for service in services:
        if int(service["id"]) == service_id: return service
    return None

def get_services_for_booking():
    services = repository.get_services()
    wanted = set(SERVICE_DEFINITIONS.keys())
    result = [s for s in services if s.get("name") in wanted]
    order = {name: index for index, name in enumerate(SERVICE_DEFINITIONS.keys())}
    result.sort(key=lambda item: order.get(item.get("name"), 999))
    return result

def service_requires_gender(service_name: str) -> bool:
    return bool(SERVICE_DEFINITIONS.get(service_name, False))

async def send_callback_message(query: CallbackQuery, text: str, components=None, delete_message=True):
    if not query.message: return
    bot = query.message.get_bot()
    chat_id = query.message.chat_id
    if delete_message:
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

    text = "📅 دریافت نوبت\n\nلطفاً خدمت مورد نظر خود را انتخاب کنید:"
    keyboard = booking_services_keyboard(services)

    if isinstance(target, CallbackQuery): await send_callback_message(target, text, components=keyboard)
    else: await target.reply(text, components=keyboard)

async def handle_booking_start(message: Message):
    user_id = message.author.id
    user = repository.get_user_by_bale_id(user_id)
    if user is None:
        await message.reply("اطلاعات کاربری شما پیدا نشد.\nلطفاً ابتدا /start را بزنید.")
        return
    state_manager.clear_state(user_id)
    state_manager.set_state(user_id, BOOKING_TARGET)
    await message.reply("📅 دریافت نوبت\n\nلطفاً مشخص کنید نوبت را برای چه کسی می‌خواهید:", components=booking_target_keyboard())

async def handle_booking_start_callback(query: CallbackQuery):
    user_id = query.user.id
    state_manager.clear_state(user_id)
    state_manager.set_state(user_id, BOOKING_TARGET)
    await send_callback_message(query, "📅 دریافت نوبت\n\nلطفاً مشخص کنید نوبت را برای چه کسی می‌خواهید:", components=booking_target_keyboard())

async def handle_booking_target_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_target:") or state_manager.get_state(user_id) != BOOKING_TARGET: return
    target = data.split(":", 1)[1]

    if target == "self":
        user, patient = get_selected_patient(user_id)
        if user is None or patient is None or not patient.get("national_id"):
            state_manager.clear_state(user_id)
            state_manager.set_state(user_id, REGISTRATION_NAME)
            from utils.keyboards import cancel_only_inline_keyboard
            bot = query.message.get_bot()
            await activate_text_keyboard(bot, query.message.chat_id, is_registered=False)
            await send_callback_message(query, "👤 برای دریافت نوبت، ابتدا باید اطلاعات شما ثبت شود.\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:\n\n(مثال: علی رضایی)", components=cancel_only_inline_keyboard("❌ لغو"))
            return
        state_manager.set_data(user_id, "booking_target", "self")
        state_manager.set_data(user_id, "booking_patient_id", patient["id"])
        state_manager.set_data(user_id, "patient_full_name", f"{patient.get('first_name','')} {patient.get('last_name','')}")
        await show_services(query, user_id)
        return

    if target == "other":
        state_manager.clear_state(user_id)
        state_manager.set_data(user_id, "booking_target", "other")
        state_manager.set_state(user_id, OTHER_PATIENT_NAME)
        bot = query.message.get_bot()
        chat_id = query.message.chat_id
        try: await query.message.delete()
        except: pass
        await activate_text_keyboard(bot, chat_id, is_registered=True)
        text = "👥 ثبت اطلاعات فرد دیگر\n\nلطفاً نام و نام خانوادگی فرد موردنظر را وارد کنید:\n\n(مثال: علی رضایی)"
        msg = await bot.send_message(chat_id, text, components=other_cancel_inline_keyboard())
        msg_id = get_msg_id(msg)
        if msg_id: 
            state_manager.set_data(user_id, "last_prompt_id", msg_id)
            state_manager.set_data(user_id, "last_prompt_text", text)

async def handle_booking_service_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_service:") or state_manager.get_state(user_id) != BOOKING_SERVICE: return
    try: service_id = int(data.split(":", 1)[1])
    except: return

    service = get_service_record(service_id)
    if service is None or service["name"] not in SERVICE_DEFINITIONS:
        await send_callback_message(query, "خدمت انتخاب‌شده معتبر نیست.", components=booking_services_keyboard(get_services_for_booking()))
        return

    state_manager.set_data(user_id, "service_id", service_id)
    state_manager.set_data(user_id, "service_name_base", service["name"])
    target = state_manager.get_data(user_id, "booking_target")

    if service_requires_gender(service["name"]):
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
    service_name = get_service_display_name(base_name, gender)

    if service_id is None or gender not in ("male", "female", "all"):
        from utils.keyboards import main_keyboard
        await send_callback_message(query, "اطلاعات رزرو ناقص است.\nلطفاً دوباره دریافت نوبت را شروع کنید.", components=main_keyboard())
        state_manager.clear_state(user_id)
        return

    dates = schedule_service.get_available_dates(service_id=service_id, gender=gender, days_ahead=7)
    availability = {}
    for d in dates:
        times = schedule_service.get_available_times(service_id=service_id, appointment_date=d, gender=gender)
        has_avail = any(int(item.get("booked_count", 0)) < int(item.get("capacity", 1)) for item in times)
        availability[d] = has_avail

    state_manager.set_data(user_id, "dates", dates)
    state_manager.set_state(user_id, BOOKING_DATE)
    await send_callback_message(query, f"🏥 خدمت انتخاب شده: {service_name}\n\nلطفاً تاریخ موردنظر را انتخاب کنید:\n\n❌ تاریخ‌های تکمیل‌شده قابل انتخاب نیستند.", components=booking_dates_keyboard(dates, service_id=service_id, gender=gender, availability=availability))

async def handle_booking_date_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_date:") or state_manager.get_state(user_id) != BOOKING_DATE: return
    appointment_date = data.split(":", 1)[1]
    dates = state_manager.get_data(user_id, "dates", [])

    if appointment_date not in dates or schedule_service.is_friday(appointment_date): return
    service_id = state_manager.get_data(user_id, "service_id")
    gender = state_manager.get_data(user_id, "gender")

    times = schedule_service.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
    has_available_time = any(int(item.get("booked_count", 0)) < int(item.get("capacity", 1)) for item in times)

    if not has_available_time:
        await show_booking_dates(query, user_id)
        return

    state_manager.set_data(user_id, "appointment_date", appointment_date)
    state_manager.set_data(user_id, "times", times)
    state_manager.set_state(user_id, BOOKING_TIME)

    base_name = state_manager.get_data(user_id, "service_name_base", "خدمت")
    service_name = get_service_display_name(base_name, gender)
    await send_callback_message(query, f"🏥 خدمت: {service_name}\n📅 تاریخ: {to_persian_date(appointment_date)}\n\nلطفاً ساعت موردنظر را انتخاب کنید:", components=booking_times_keyboard(times, appointment_date))

async def handle_booking_time_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_time:") or state_manager.get_state(user_id) != BOOKING_TIME: return
    parts = data.split(":", 2)
    if len(parts) != 3: return
    appointment_date, start_time = parts[1], parts[2]

    service_id = state_manager.get_data(user_id, "service_id")
    gender = state_manager.get_data(user_id, "gender")

    if not schedule_service.is_slot_available(service_id=service_id, appointment_date=appointment_date, start_time=start_time, gender=gender):
        times = schedule_service.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
        await send_callback_message(query, "⚠️ این ظرفیت همین الان پر شد.\n\nلطفاً ساعت دیگری انتخاب کنید.", components=booking_times_keyboard(times, appointment_date))
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
    service_name = get_service_display_name(base_name, gender)
    patient_name = state_manager.get_data(user_id, "patient_full_name", "بیمار")
    gender_text = "آقا" if gender == "male" else ("خانم" if gender == "female" else "عمومی")

    summary_text = (
        "📋 پیش‌فاکتور و تأیید نهایی نوبت\n\n"
        f"👤 بیمار: {patient_name}\n"
        f"🏥 خدمت: {service_name}\n"
        f"⚧ جنسیت: {gender_text}\n"
        f"📅 تاریخ: {to_date_label(appointment_date)}\n"
        f"🕐 ساعت: {start_time}\n\n"
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
        from utils.helpers import send_welcome_message
        await send_callback_message(query, "❌ فرآیند دریافت نوبت لغو شد.", components=main_keyboard())
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
        service_name = get_service_display_name(base_name, gender)

        if not schedule_service.is_slot_available(service_id=service_id, appointment_date=appointment_date, start_time=start_time, gender=gender):
            times = schedule_service.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
            state_manager.set_state(user_id, BOOKING_TIME)
            await send_callback_message(query, "⚠️ متاسفانه در همین چند لحظه ظرفیت این ساعت پر شد.\nلطفاً ساعت دیگری انتخاب کنید.", components=booking_times_keyboard(times, appointment_date))
            return

        user, patient = get_selected_patient(user_id)

        if target == "other":
            try:
                patient_id = repository.create_patient(
                    user_id=None, national_id=data_cache["other_national_id"], first_name=data_cache["other_first_name"],
                    last_name=data_cache["other_last_name"], phone_number=data_cache["other_phone"], birth_date=None,
                    gender=data_cache["other_gender"], insurance=data_cache["other_insurance"]
                )
                repository.add_patient_profile(user["id"], patient_id)
            except Exception:
                from utils.keyboards import clinic_info_keyboard
                await send_callback_message(query, "❌ خطا در ذخیره اطلاعات. لطفاً مجدداً تلاش کنید.", components=clinic_info_keyboard())
                state_manager.clear_state(user_id)
                return
        else:
            if not patient: 
                from utils.keyboards import clinic_info_keyboard
                await send_callback_message(query, "❌ خطای دسترسی به اطلاعات شما.", components=clinic_info_keyboard())
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
                    "🔹 **راهنما:**\n"
                    "• جهت مشاهده جزئیات نوبت و یا لغو آن، لطفاً از منوی **«📋 نوبت‌های من»** اقدام کنید.\n"
                    "• در صورتی که قصد دارید برای شخص دیگری (بجز خودتان) نوبت بگیرید، از منوی دریافت نوبت گزینه **«👥 برای شخص دیگر»** را انتخاب نمایید."
                )
                await send_callback_message(query, error_msg, components=back_to_services_keyboard())
                return
            else:
                from utils.keyboards import clinic_info_keyboard
                await send_callback_message(query, "❌ خطا در ثبت نوبت. لطفاً دوباره تلاش کنید.", components=clinic_info_keyboard())
                state_manager.clear_state(user_id)
                return
        except Exception:
            from utils.keyboards import clinic_info_keyboard
            await send_callback_message(query, "❌ خطا در ثبت نوبت. لطفاً دوباره تلاش کنید.", components=clinic_info_keyboard())
            state_manager.clear_state(user_id)
            return

        if appointment_id is None:
            state_manager.set_state(user_id, BOOKING_TIME)
            times = schedule_service.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
            await send_callback_message(query, "⚠️ متاسفانه در همین لحظه ظرفیت این ساعت پر شد.\nلطفاً ساعت دیگری انتخاب کنید.", components=booking_times_keyboard(times, appointment_date))
            return

        state_manager.clear_state(user_id)
        
        success_msg = (
            f"✅ نوبت با موفقیت ثبت نهایی شد.\n\n"
            f"🏥 خدمت: {service_name}\n"
            f"📅 تاریخ: {to_persian_date(appointment_date)}\n"
            f"🕐 ساعت: {start_time}\n"
            f"🔖 کد پیگیری: CF-{appointment_id:06d}\n\n\n"
            f"🔸 جهت مشاهده جزئیات نوبت و یا لغو آن، از منوی «📋 نوبت‌های من» اقدام کنید.\n\n"
            f"🔸 امکان لغو نوبت تنها تا ۲۴ ساعت قبل* از زمان رزرو وجود دارد."
        )
        await send_callback_message(query, success_msg, components=booking_confirmation_keyboard())

async def handle_booking_back_callback(query: CallbackQuery):
    user_id = query.user.id
    data = query.data or ""
    if not data.startswith("booking_back:"): return
    destination = data.split(":", 1)[1]

    if destination == "home":
        state_manager.clear_state(user_id)
        from utils.helpers import send_welcome_message
        await send_welcome_message(query, user_id)
        return
    if destination == "target":
        state_manager.clear_state(user_id)
        state_manager.set_state(user_id, BOOKING_TARGET)
        await send_callback_message(query, "📅 دریافت نوبت\n\nنوبت را برای چه کسی می‌خواهید؟", components=booking_target_keyboard())
        return
    if destination == "services":
        await show_services(query, user_id)
        return
    if destination == "dates":
        service_id = state_manager.get_data(user_id, "service_id")
        gender = state_manager.get_data(user_id, "gender")
        dates = state_manager.get_data(user_id, "dates", [])
        state_manager.set_state(user_id, BOOKING_DATE)
        await send_callback_message(query, "📅 لطفاً تاریخ موردنظر را انتخاب کنید:\n\n❌ تاریخ‌های تکمیل‌شده قابل انتخاب نیستند.", components=booking_dates_keyboard(dates, service_id, gender))
        return

async def process_booking_message(message: Message) -> bool:
    user_id = message.author.id
    state = state_manager.get_state(user_id)
    if state is None: return False
    value = (message.text or "").strip()

    if not value: return True

    if state == OTHER_PATIENT_NAME:
        normalized = " ".join(value.split())
        if not validate_full_name(normalized):
            await send_tracked_message(message, user_id, "نام معتبر نیست.\n\n(مثال: علی رضایی)", components=other_cancel_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        parts = normalized.split()
        state_manager.set_data(user_id, "other_first_name", parts[0])
        state_manager.set_data(user_id, "other_last_name", " ".join(parts[1:]))
        state_manager.set_data(user_id, "patient_full_name", normalized)
        state_manager.set_state(user_id, OTHER_PATIENT_NATIONAL_ID)
        await send_tracked_message(message, user_id, "💳 لطفاً کد ملی ۱۰ رقمی را وارد کنید:\n\n(مثال: 0012345678)", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_NATIONAL_ID:
        if not validate_national_id(value):
            await send_tracked_message(message, user_id, "کد ملی نامعتبر است.", components=other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "other_national_id", value)
        state_manager.set_state(user_id, OTHER_PATIENT_PHONE)
        await send_tracked_message(message, user_id, "📱 لطفاً شماره موبایل را وارد کنید:\n\n(مثال: 09123456789)", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_PHONE:
        if not validate_phone_number(value):
            await send_tracked_message(message, user_id, "شماره موبایل نامعتبر است.", components=other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "other_phone", value)
        state_manager.set_state(user_id, OTHER_PATIENT_GENDER)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
        await send_tracked_message(message, user_id, "⚧ لطفاً جنسیت را انتخاب کنید:", components=other_back_inline_keyboard())
        return True

    if state == OTHER_PATIENT_GENDER:
        if value not in GENDER_MAP:
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
            await send_tracked_message(message, user_id, "لطفاً منحصراً از دکمه‌های پایین صفحه استفاده کنید.", components=other_back_inline_keyboard())
            return True
            
        await safe_delete_previous_inline(message, user_id)
        
        state_manager.set_data(user_id, "other_insurance", INSURANCE_MAP[value])
        
        await message.reply("✅ اطلاعات فرد دریافت شد.\nدر حال انتقال به بخش انتخاب خدمات...", components=main_keyboard())
        await show_services(message, user_id)
        return True

    if state in (BOOKING_SERVICE, BOOKING_DATE, BOOKING_TIME, BOOKING_CHECKOUT):
        await message.reply("لطفاً از طریق دکمه‌های شیشه‌ای نمایش‌داده‌شده در بالا انتخاب خود را انجام دهید.")
        return True

    return False