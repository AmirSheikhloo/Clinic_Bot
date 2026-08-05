import asyncio
from bale import Message, CallbackQuery

from database.repository import repository
from utils.keyboards import (
    patient_keyboard, gender_keyboard, insurance_keyboard, register_keyboard, main_keyboard, 
    cancel_only_inline_keyboard, cancel_back_inline_keyboard,
    edit_cancel_inline_keyboard, edit_back_inline_keyboard
)
from utils.state_manager import state_manager
from utils.validators import validate_full_name, validate_national_id, validate_phone_number, normalize_digits
from utils.helpers import send_welcome_message, get_msg_id, activate_text_keyboard

REGISTRATION_NATIONAL_ID = "registration_national_id"
REGISTRATION_NAME = "registration_name"
REGISTRATION_PHONE = "registration_phone"
REGISTRATION_GENDER = "registration_gender"
REGISTRATION_INSURANCE = "registration_insurance"

EDIT_NAME = "edit_name"
EDIT_NATIONAL_ID = "edit_national_id"
EDIT_PHONE = "edit_phone"
EDIT_GENDER = "edit_gender"
EDIT_INSURANCE = "edit_insurance"

INSURANCE_OPTIONS = {"سلامت": "health", "تأمین اجتماعی": "social_security", "تامین اجتماعی": "social_security", "نیروهای مسلح": "armed_forces", "بدون بیمه": "none"}
GENDER_OPTIONS = {"آقا": "male", "خانم": "female"}
GENDER_DISPLAY = {"male": "آقا", "female": "خانم"}
INSURANCE_DISPLAY = {"health": "سلامت", "social_security": "تأمین اجتماعی", "armed_forces": "نیروهای مسلح", "none": "بدون بیمه"}

async def safe_delete_previous_inline(message, user_id: int):
    last_id = state_manager.get_data(user_id, "last_prompt_id")
    last_text = state_manager.get_data(user_id, "last_prompt_text")
    if last_id and last_text:
        try:
            bot = message.get_bot() if hasattr(message, "get_bot") else None
            if bot: await bot.edit_message(message.chat_id, last_id, text=last_text, components=None)
        except:
            pass
        state_manager.set_data(user_id, "last_prompt_id", None)
        state_manager.set_data(user_id, "last_prompt_text", None)

async def send_tracked_message(message, user_id: int, text: str, components=None):
    msg = await message.reply(text, components=components)
    msg_id = get_msg_id(msg)
    if msg_id: 
        state_manager.set_data(user_id, "last_prompt_id", msg_id)
        state_manager.set_data(user_id, "last_prompt_text", text)

async def handle_patient_registration(message: Message) -> None:
    user_id = message.author.id
    user = repository.get_user_by_bale_id(user_id)

    if user is None:
        repository.create_user(bale_user_id=user_id, username=message.author.username, first_name=message.author.first_name, last_name=message.author.last_name)
        user = repository.get_user_by_bale_id(user_id)

    patient = repository.get_patient_by_user_id(user["id"])
    if patient is not None and patient.get("national_id"):
        await message.reply("✅ اطلاعات بیمار شما قبلاً ثبت شده است.", components=main_keyboard())
        return

    state_manager.clear_state(user_id)
    state_manager.set_state(user_id, REGISTRATION_NATIONAL_ID)
    
    await activate_text_keyboard(message.get_bot(), message.chat_id, is_registered=False)

    await send_tracked_message(message, user_id,
        "✨ کاربر گرامی، جهت بررسی پرونده یا ثبت‌نام جدید، لطفاً ابتدا کد ملی ۱۰ رقمی خود را وارد کنید:\n\n"
        "(مثال: 0012345678)",
        components=cancel_only_inline_keyboard("❌ لغو ثبت‌نام")
    )

async def process_registration_message(message: Message) -> bool:
    user_id = message.author.id
    state = state_manager.get_state(user_id)
    if state is None: return False

    value = (message.text or "").strip()

    if not value:
        await message.reply("⚠️ لطفاً یک مقدار معتبر وارد نمایید.")
        return True

    if state == REGISTRATION_NATIONAL_ID:
        if not validate_national_id(value):
            await send_tracked_message(message, user_id, "کد ملی واردشده معتبر نمی‌باشد.\nکد ملی باید دقیقاً ۱۰ رقم باشد و از الگوریتم صحیح پیروی کند. لطفاً مجدداً بررسی و ارسال کنید.", components=cancel_only_inline_keyboard("❌ لغو ثبت‌نام"))
            return True
            
        value = normalize_digits(value)
        
        existing_patient = repository.get_patient_by_national_id(value)
        
        if existing_patient:
            await safe_delete_previous_inline(message, user_id)
            user = repository.get_user_by_bale_id(user_id)
            
            repository.update_patient(patient_id=existing_patient["id"], user_id=user["id"])
            repository.add_patient_profile(user["id"], existing_patient["id"])
            
            state_manager.clear_state(user_id)
            await message.reply(f"✅ پرونده شما در سیستم یافت شد!\nخوش برگشتید {existing_patient['first_name']} {existing_patient['last_name']} عزیز.")
            await send_welcome_message(message, user_id)
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "national_id", value)
        state_manager.set_state(user_id, REGISTRATION_NAME)
        await send_tracked_message(message, user_id, "👤 این کد ملی در سیستم ثبت نشده است. بیایید یک پرونده جدید بسازیم!\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:\n\n(مثال: علی رضایی)", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
        return True

    if state == REGISTRATION_NAME:
        normalized_name = " ".join(value.split())
        parts = normalized_name.split(" ")
        if len(parts) < 2 or not validate_full_name(normalized_name):
            await send_tracked_message(message, user_id, "نام و نام خانوادگی واردشده صحیح نیست.\nلطفاً نام را به صورت کامل و با حروف فارسی وارد کنید.\n\n(مثال: علی رضایی)", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return True
        
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "first_name", parts[0])
        state_manager.set_data(user_id, "last_name", " ".join(parts[1:]))
        state_manager.set_state(user_id, REGISTRATION_PHONE)
        await send_tracked_message(message, user_id, "📱 لطفاً شماره موبایل خود را وارد نمایید:\n\n(مثال: 09123456789)", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
        return True

    if state == REGISTRATION_PHONE:
        if not validate_phone_number(value):
            await send_tracked_message(message, user_id, "شماره موبایل واردشده صحیح نیست.\nشماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return True
            
        value = normalize_digits(value)
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "phone_number", value)
        state_manager.set_state(user_id, REGISTRATION_GENDER)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
        await send_tracked_message(message, user_id, "⚧ لطفاً جنسیت خود را انتخاب کنید:", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
        return True

    if state == REGISTRATION_GENDER:
        if value not in GENDER_OPTIONS:
            await send_tracked_message(message, user_id, "لطفاً جنسیت خود را منحصراً از دکمه‌های پایین صفحه انتخاب کنید.", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "gender", GENDER_OPTIONS[value])
        state_manager.set_state(user_id, REGISTRATION_INSURANCE)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=insurance_keyboard())
        await send_tracked_message(message, user_id, "🏥 لطفاً نوع بیمه درمانی خود را انتخاب نمایید:", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
        return True

    if state == REGISTRATION_INSURANCE:
        if value not in INSURANCE_OPTIONS:
            await send_tracked_message(message, user_id, "لطفاً بیمه خود را منحصراً از دکمه‌های پایین صفحه انتخاب کنید.", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "insurance", INSURANCE_OPTIONS[value])
        data = state_manager.get_all_data(user_id)
        user = repository.get_user_by_bale_id(user_id)

        try:
            repository.create_patient(
                user_id=user["id"], national_id=data["national_id"], first_name=data["first_name"],
                last_name=data["last_name"], phone_number=data["phone_number"], birth_date=None,
                gender=data["gender"], insurance=data["insurance"]
            )
            repository.update_user_phone(bale_user_id=user_id, phone_number=data["phone_number"])
        except Exception:
            await message.reply("❌ متأسفانه هنگام ثبت اطلاعات خطایی رخ داد. لطفاً دوباره تلاش کنید.", components=register_keyboard())
            state_manager.clear_state(user_id)
            return True

        state_manager.clear_state(user_id)
        await message.reply("✅ اطلاعات شما با موفقیت در سامانه درمانگاه ثبت شد.", components=main_keyboard())
        await send_welcome_message(message, user_id)
        return True

    return await process_edit_message(message, state, value)

async def handle_patient_lookup(update) -> None:
    if isinstance(update, CallbackQuery):
        user_id = update.user.id
        bot = update.message.get_bot()
        chat_id = update.message.chat_id
    else:
        user_id = update.author.id
        bot = update.get_bot()
        chat_id = update.chat_id

    user = repository.get_user_by_bale_id(user_id)
    
    async def send_reply(text, kb):
        await bot.send_message(chat_id, text, components=kb)

    if user is None:
        await send_reply("اطلاعات کاربری شما در سامانه پیدا نشد.", main_keyboard())
        return
    patient = repository.get_patient_by_user_id(user["id"])
    if patient is None or not patient.get("national_id"):
        await send_reply("هنوز اطلاعات بیمار شما کامل ثبت نشده است.", register_keyboard())
        return

    await send_reply(
        "🪪 **پروفایل کاربری شما در درمانگاه**\n\n"
        f"👤 **نام و نام خانوادگی:** {patient.get('first_name', '')} {patient.get('last_name', '')}\n"
        f"💳 **کد ملی:** {patient.get('national_id') or 'ثبت نشده'}\n"
        f"📱 **شماره تماس:** {patient.get('phone_number') or 'ثبت نشده'}\n"
        f"⚧ **جنسیت:** {GENDER_DISPLAY.get(patient.get('gender'), 'ثبت نشده')}\n"
        f"🏥 **نوع بیمه:** {INSURANCE_DISPLAY.get(patient.get('insurance'), 'ثبت نشده')}\n\n"
        "جهت ویرایش اطلاعات، می‌توانید از دکمه زیر استفاده نمایید 👇",
        patient_keyboard(),
    )

async def handle_patient_edit(query: CallbackQuery) -> None:
    user_id = query.user.id
    bot = query.message.get_bot()
    chat_id = query.message.chat_id
    
    try: await query.message.delete()
    except: pass

    user = repository.get_user_by_bale_id(user_id)
    patient = repository.get_patient_by_user_id(user["id"]) if user else None

    async def send_msg(text, kb):
        msg = await bot.send_message(chat_id, text, components=kb)
        msg_id = get_msg_id(msg)
        if msg_id: 
            state_manager.set_data(user_id, "last_prompt_id", msg_id)
            state_manager.set_data(user_id, "last_prompt_text", text)

    if patient is None:
        await send_msg("ابتدا باید اطلاعات بیمار خود را ثبت کنید.", register_keyboard())
        return

    state_manager.clear_state(user_id)
    state_manager.set_data(user_id, "edit_patient_id", patient["id"])
    state_manager.set_state(user_id, EDIT_NAME)

    await activate_text_keyboard(bot, chat_id, is_registered=True)

    await send_msg(
        "✏️ **به‌روزرسانی اطلاعات بیمار**\n\n"
        "👤 لطفاً نام و نام خانوادگی جدید خود را وارد کنید:\n\n"
        "(مثال: علی رضایی)\n\n"
        "⚠️ توجه: تا پایان تمامی مراحل، اطلاعات قبلی شما تغییر نخواهد کرد.",
        edit_cancel_inline_keyboard("❌ لغو ویرایش")
    )

async def process_edit_message(message: Message, state: str, value: str) -> bool:
    user_id = message.author.id
    user = repository.get_user_by_bale_id(user_id)
    patient = repository.get_patient_by_user_id(user["id"]) if user else None
    if patient is None:
        state_manager.clear_state(user_id)
        return False

    if state == EDIT_NAME:
        normalized_name = " ".join(value.split())
        parts = normalized_name.split(" ")
        if len(parts) < 2 or not validate_full_name(normalized_name):
            await send_tracked_message(message, user_id, "نام نامعتبر است. لطفاً نام کامل خود را با حروف فارسی وارد کنید.", components=edit_cancel_inline_keyboard("❌ لغو ویرایش"))
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_first_name", parts[0])
        state_manager.set_data(user_id, "edit_last_name", " ".join(parts[1:]))
        state_manager.set_state(user_id, EDIT_NATIONAL_ID)
        await send_tracked_message(message, user_id, "✅ نام دریافت شد.\n\n💳 لطفاً کد ملی ۱۰ رقمی جدید خود را وارد کنید:\n\n(مثال: 0012345678)", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
        return True

    if state == EDIT_NATIONAL_ID:
        if not validate_national_id(value):
            await send_tracked_message(message, user_id, "کد ملی نامعتبر است. لطفاً مجدداً بررسی کنید.", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return True
            
        value = normalize_digits(value)
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_national_id", value)
        state_manager.set_state(user_id, EDIT_PHONE)
        await send_tracked_message(message, user_id, "✅ کد ملی دریافت شد.\n\n📱 لطفاً شماره موبایل جدید خود را وارد نمایید:\n\n(مثال: 09123456789)", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
        return True

    if state == EDIT_PHONE:
        if not validate_phone_number(value):
            await send_tracked_message(message, user_id, "شماره موبایل نامعتبر است. لطفاً مجدداً بررسی کنید.", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return True
            
        value = normalize_digits(value)
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_phone_number", value)
        state_manager.set_state(user_id, EDIT_GENDER)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
        await send_tracked_message(message, user_id, "✅ شماره موبایل دریافت شد.\n\n⚧ لطفاً جنسیت خود را انتخاب کنید:", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
        return True

    if state == EDIT_GENDER:
        if value not in GENDER_OPTIONS:
            await send_tracked_message(message, user_id, "لطفاً جنسیت خود را از دکمه‌های پایین صفحه انتخاب کنید.", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_gender", GENDER_OPTIONS[value])
        state_manager.set_state(user_id, EDIT_INSURANCE)
        
        await message.reply("لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=insurance_keyboard())
        await send_tracked_message(message, user_id, "✅ جنسیت دریافت شد.\n\n🏥 لطفاً نوع بیمه درمانی خود را انتخاب کنید:", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
        return True

    if state == EDIT_INSURANCE:
        if value not in INSURANCE_OPTIONS:
            await send_tracked_message(message, user_id, "لطفاً بیمه خود را از دکمه‌های پایین صفحه انتخاب کنید.", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return True
            
        await safe_delete_previous_inline(message, user_id)
        state_manager.set_data(user_id, "edit_insurance", INSURANCE_OPTIONS[value])
        data = state_manager.get_all_data(user_id)

        try:
            try:
                repository.update_patient(
                    patient_id=patient["id"], first_name=data["edit_first_name"], last_name=data["edit_last_name"],
                    phone_number=data["edit_phone_number"], birth_date=patient.get("birth_date"),
                    gender=data["edit_gender"], insurance=data["edit_insurance"], national_id=data["edit_national_id"]
                )
            except TypeError:
                repository.update_patient(
                    patient_id=patient["id"], first_name=data["edit_first_name"], last_name=data["edit_last_name"],
                    phone_number=data["edit_phone_number"], birth_date=patient.get("birth_date"),
                    gender=data["edit_gender"], insurance=data["edit_insurance"]
                )
            repository.update_user_phone(bale_user_id=user_id, phone_number=data["edit_phone_number"])
        except Exception:
            state_manager.clear_state(user_id)
            await message.reply("❌ متأسفانه در ثبت تغییرات خطایی رخ داد.", components=main_keyboard())
            await send_welcome_message(message, user_id)
            return True

        state_manager.clear_state(user_id)
        await message.reply("✅ پروفایل شما با موفقیت به‌روزرسانی شد.", components=main_keyboard())
        await handle_patient_lookup(message)
        return True

    return False