import asyncio
from bale import CallbackQuery

from handlers.booking import (
    handle_booking_target_callback,
    handle_booking_service_callback,
    handle_booking_date_callback,
    handle_booking_time_callback,
    handle_booking_checkout_callback,
    handle_booking_back_callback,
    handle_booking_start_callback,
    OTHER_PATIENT_NAME, OTHER_PATIENT_NATIONAL_ID, OTHER_PATIENT_PHONE, OTHER_PATIENT_GENDER, OTHER_PATIENT_INSURANCE
)

from handlers.appointments import (
    handle_appointment_callback,
)

from handlers.patients import (
    handle_patient_edit, handle_patient_lookup, REGISTRATION_NAME, REGISTRATION_NATIONAL_ID, REGISTRATION_PHONE, REGISTRATION_GENDER, REGISTRATION_INSURANCE,
    EDIT_NAME, EDIT_NATIONAL_ID, EDIT_PHONE, EDIT_GENDER, EDIT_INSURANCE
)
from utils.state_manager import state_manager
from utils.helpers import send_welcome_message, get_msg_id, activate_text_keyboard
from utils.keyboards import (
    cancel_only_inline_keyboard, cancel_back_inline_keyboard, edit_cancel_inline_keyboard, edit_back_inline_keyboard,
    other_cancel_inline_keyboard, other_back_inline_keyboard, gender_keyboard, insurance_keyboard, main_keyboard
)

async def send_callback_message(query: CallbackQuery, text: str, components=None):
    bot = query.message.get_bot()
    try: await query.message.delete()
    except: pass
    msg = await bot.send_message(query.message.chat_id, text, components=components)
    msg_id = get_msg_id(msg)
    if msg_id: 
        state_manager.set_data(query.user.id, "last_prompt_id", msg_id)
        state_manager.set_data(query.user.id, "last_prompt_text", text)

async def handle_callback(query: CallbackQuery) -> None:
    data = query.data or ""
    user_id = query.user.id
    if not data:
        return

    if data.startswith("ignore:"):
        return

    if data == "booking_start_inline":
        await handle_booking_start_callback(query)
        return

    if data == "register_cancel":
        state_manager.clear_state(user_id)
        bot = query.message.get_bot()
        try: await query.message.delete()
        except: pass
        await bot.send_message(query.message.chat_id, "❌ فرایند متوقف شد.", components=main_keyboard())
        await send_welcome_message(query, user_id)
        return

    if data == "patient:edit_cancel":
        state_manager.clear_state(user_id)
        bot = query.message.get_bot()
        try: await query.message.delete()
        except: pass
        await bot.send_message(query.message.chat_id, "❌ فرایند ویرایش لغو شد.", components=main_keyboard())
        await handle_patient_lookup(query)
        return

    if data == "patient:edit":
        await handle_patient_edit(query)
        return

    if data == "register_back":
        state = state_manager.get_state(user_id)
        bot = query.message.get_bot()
        chat_id = query.message.chat_id
        
        if state == REGISTRATION_NATIONAL_ID:
            state_manager.set_state(user_id, REGISTRATION_NAME)
            await send_callback_message(query, "✨ کاربر گرامی، جهت تکمیل پرونده الکترونیک خود، لطفاً نام و نام خانوادگی خود را وارد کنید:\n\n(مثال: علی رضایی)", components=cancel_only_inline_keyboard("❌ لغو ثبت‌نام"))
            return
        elif state == REGISTRATION_PHONE:
            state_manager.set_state(user_id, REGISTRATION_NATIONAL_ID)
            await send_callback_message(query, "💳 لطفاً کد ملی ۱۰ رقمی خود را وارد کنید:\n\n(مثال: 0012345678)", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return
        elif state == REGISTRATION_GENDER:
            state_manager.set_state(user_id, REGISTRATION_PHONE)
            await activate_text_keyboard(bot, chat_id, is_registered=False)
            await send_callback_message(query, "📱 لطفاً شماره موبایل خود را وارد نمایید:\n\n(مثال: 09123456789)", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return
        elif state == REGISTRATION_INSURANCE:
            state_manager.set_state(user_id, REGISTRATION_GENDER)
            await bot.send_message(chat_id, "لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
            await send_callback_message(query, "⚧ لطفاً جنسیت خود را انتخاب کنید:", components=cancel_back_inline_keyboard("❌ لغو ثبت‌نام"))
            return

    if data == "edit_back":
        state = state_manager.get_state(user_id)
        bot = query.message.get_bot()
        chat_id = query.message.chat_id
        
        if state == EDIT_NATIONAL_ID:
            state_manager.set_state(user_id, EDIT_NAME)
            await send_callback_message(query, "✏️ **به‌روزرسانی اطلاعات بیمار**\n\n👤 لطفاً نام و نام خانوادگی جدید خود را وارد کنید:\n\n(مثال: علی رضایی)", components=edit_cancel_inline_keyboard("❌ لغو ویرایش"))
            return
        elif state == EDIT_PHONE:
            state_manager.set_state(user_id, EDIT_NATIONAL_ID)
            await send_callback_message(query, "💳 لطفاً کد ملی ۱۰ رقمی جدید خود را وارد کنید:\n\n(مثال: 0012345678)", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return
        elif state == EDIT_GENDER:
            state_manager.set_state(user_id, EDIT_PHONE)
            await activate_text_keyboard(bot, chat_id, is_registered=True)
            await send_callback_message(query, "📱 لطفاً شماره موبایل جدید خود را وارد نمایید:\n\n(مثال: 09123456789)", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return
        elif state == EDIT_INSURANCE:
            state_manager.set_state(user_id, EDIT_GENDER)
            await bot.send_message(chat_id, "لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
            await send_callback_message(query, "⚧ لطفاً جنسیت خود را انتخاب کنید:", components=edit_back_inline_keyboard("❌ لغو ویرایش"))
            return

    if data == "other_back":
        state = state_manager.get_state(user_id)
        bot = query.message.get_bot()
        chat_id = query.message.chat_id
        
        if state == OTHER_PATIENT_NATIONAL_ID:
            state_manager.set_state(user_id, OTHER_PATIENT_NAME)
            await send_callback_message(query, "👥 ثبت اطلاعات فرد دیگر\n\nلطفاً نام و نام خانوادگی فرد موردنظر را وارد کنید:\n\n(مثال: علی رضایی)", components=other_cancel_inline_keyboard())
            return
        elif state == OTHER_PATIENT_PHONE:
            state_manager.set_state(user_id, OTHER_PATIENT_NATIONAL_ID)
            await send_callback_message(query, "💳 لطفاً کد ملی ۱۰ رقمی را وارد کنید:\n\n(مثال: 0012345678)", components=other_back_inline_keyboard())
            return
        elif state == OTHER_PATIENT_GENDER:
            state_manager.set_state(user_id, OTHER_PATIENT_PHONE)
            await activate_text_keyboard(bot, chat_id, is_registered=True)
            await send_callback_message(query, "📱 لطفاً شماره موبایل را وارد کنید:\n\n(مثال: 09123456789)", components=other_back_inline_keyboard())
            return
        elif state == OTHER_PATIENT_INSURANCE:
            state_manager.set_state(user_id, OTHER_PATIENT_GENDER)
            await bot.send_message(chat_id, "لطفاً از منوی بازشده در پایین صفحه استفاده کنید:", components=gender_keyboard())
            await send_callback_message(query, "⚧ لطفاً جنسیت را انتخاب کنید:", components=other_back_inline_keyboard())
            return

    if (
        data.startswith("appointments:")
        or data.startswith("appointment_current:")
        or data.startswith("appointment_history:")
        or data.startswith("appointment_cancel:")
        or data.startswith("appointment_cancel_confirm:")
        or data.startswith("appointment_cancel_abort:")
    ):
        await handle_appointment_callback(query)
        return

    if data.startswith("booking_target:"):
        await handle_booking_target_callback(query)
        return

    if data.startswith("booking_back:"):
        await handle_booking_back_callback(query)
        return

    if data.startswith("booking_service:"):
        await handle_booking_service_callback(query)
        return

    if data.startswith("booking_date:"):
        await handle_booking_date_callback(query)
        return

    if data.startswith("booking_time:"):
        await handle_booking_time_callback(query)
        return

    if data.startswith("booking_checkout:"):
        await handle_booking_checkout_callback(query)
        return