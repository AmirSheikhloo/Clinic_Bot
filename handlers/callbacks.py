from bale import CallbackQuery


from handlers.booking import (
    handle_booking_target_callback,
    handle_booking_service_callback,
    handle_booking_gender_callback,
    handle_booking_date_callback,
    handle_booking_time_callback,
    handle_booking_back_callback,
)


from handlers.appointments import (
    handle_appointment_callback,
)


async def handle_callback(
    query: CallbackQuery,
) -> None:

    data = query.data or ""

    if not data:
        return

    # =====================================================
    # Appointments
    # =====================================================

    if (
        data.startswith(
            "appointments:"
        )
        or data.startswith(
            "appointment_current:"
        )
        or data.startswith(
            "appointment_history:"
        )
        or data.startswith(
            "appointment_cancel:"
        )
        or data.startswith(
            "appointment_cancel_confirm:"
        )
        or data.startswith(
            "appointment_cancel_abort:"
        )
    ):

        await handle_appointment_callback(
            query
        )

        return

    # =====================================================
    # Booking - Target
    # =====================================================

    if data.startswith(
        "booking_target:"
    ):

        await handle_booking_target_callback(
            query
        )

        return

    # =====================================================
    # Booking - Gender
    # =====================================================

    if data.startswith(
        "booking_gender:"
    ):

        await handle_booking_gender_callback(
            query
        )

        return

    # =====================================================
    # Booking - Back
    # =====================================================

    if data.startswith(
        "booking_back:"
    ):

        await handle_booking_back_callback(
            query
        )

        return

    # =====================================================
    # Booking - Service
    # =====================================================

    if data.startswith(
        "booking_service:"
    ):

        await handle_booking_service_callback(
            query
        )

        return

    # =====================================================
    # Booking - Date
    # =====================================================

    if data.startswith(
        "booking_date:"
    ):

        await handle_booking_date_callback(
            query
        )

        return

    # =====================================================
    # Booking - Time
    # =====================================================

    if data.startswith(
        "booking_time:"
    ):

        await handle_booking_time_callback(
            query
        )

        return