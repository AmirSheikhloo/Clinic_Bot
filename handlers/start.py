from bale import Message
from database.repository import repository
from utils.helpers import send_welcome_message
from handlers.patients import handle_patient_registration

async def handle_start(message: Message) -> None:
    user_id = message.author.id
    user = repository.get_user_by_bale_id(user_id)

    if user is None:
        repository.create_user(
            bale_user_id=user_id,
            username=message.author.username,
            first_name=message.author.first_name,
            last_name=message.author.last_name,
        )
        user = repository.get_user_by_bale_id(user_id)
        
    patient = repository.get_patient_by_user_id(user["id"]) if user else None

    if patient and patient.get("national_id"):
        await send_welcome_message(message, user_id)
    else:
        await handle_patient_registration(message)