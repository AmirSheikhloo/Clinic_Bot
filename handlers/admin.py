from bale import Message

from database.repository import repository


async def handle_admin_panel(
    message: Message,
) -> None:

    await message.reply(
        "پنل مدیریت درمانگاه\n\n"
        "/pending - نوبت‌های ثبت‌شده\n"
        "/schedule - مدیریت ظرفیت و ساعات\n"
        "/patients - مدیریت بیماران"
    )


async def handle_pending_appointments(
    message: Message,
) -> None:

    appointments = repository.get_pending_appointments()

    if not appointments:
        await message.reply(
            "در حال حاضر نوبت ثبت‌شده‌ای وجود ندارد."
        )
        return

    lines = [
        "📋 نوبت‌های ثبت‌شده:\n"
    ]

    for appointment in appointments:

        gender = (
            "آقا"
            if appointment["gender"] == "male"
            else "خانم"
        )

        lines.append(
            f"🔢 نوبت: {appointment['id']}\n"
            f"👤 بیمار: "
            f"{appointment['patient_first_name']} "
            f"{appointment['patient_last_name']}\n"
            f"🏥 خدمت: {appointment['service_name']}\n"
            f"👤 جنسیت: {gender}\n"
            f"📅 تاریخ: {appointment['appointment_date']}\n"
            f"⏰ ساعت: {appointment['start_time']}\n"
        )

    await message.reply(
        "\n".join(lines)
    )


async def handle_manage_schedule(
    message: Message,
) -> None:

    await message.reply(
        "مدیریت برنامه و ظرفیت از طریق پنل مدیریت انجام می‌شود."
    )


async def handle_manage_patients(
    message: Message,
) -> None:

    patients = repository.get_all_patients()

    if not patients:
        await message.reply(
            "بیماری ثبت نشده است."
        )
        return

    lines = [
        "👥 بیماران:\n"
    ]

    for patient in patients:

        lines.append(
            f"🆔 {patient['id']} - "
            f"{patient['first_name']} "
            f"{patient['last_name']}\n"
            f"📱 {patient['phone_number']}\n"
            f"کد ملی: {patient['national_id']}\n"
        )

    await message.reply(
        "\n".join(lines)
    )