from bale import Message

from database.repository import repository

from utils.keyboards import (
    main_keyboard,
)


async def handle_start(
    message: Message,
) -> None:

    user_id = message.author.id

    user = (
        repository.get_user_by_bale_id(
            user_id
        )
    )

    if user is None:

        repository.create_user(
            bale_user_id=user_id,
            username=(
                message.author.username
            ),
            first_name=(
                message.author.first_name
            ),
            last_name=(
                message.author.last_name
            ),
        )

    await message.reply(
        "🏥 درمانگاه فرهنگیان\n\n"
        "به سامانه نوبت‌دهی "
        "درمانگاه فرهنگیان خوش آمدید.\n\n"
        "لطفاً یکی از گزینه‌های زیر "
        "را انتخاب کنید:",
        components=main_keyboard(),
    )