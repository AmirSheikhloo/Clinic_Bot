from datetime import date, timedelta

from database.repository import repository


# =========================================================
# Default Settings
# =========================================================

DEFAULT_SETTINGS = {
    "clinic_name": "درمانگاه فرهنگیان",
    "clinic_phone": "",
    "clinic_address": "",
    "working_days": (
        "Saturday,Sunday,Monday,Tuesday,"
        "Wednesday,Thursday"
    ),
    "working_hours": (
        "14:00,15:00,16:00,17:00"
    ),
    "timezone": "Asia/Tehran",
    "appointment_duration": "30",
}


# =========================================================
# Required Services
# =========================================================

REQUIRED_SERVICES = [
    "ویزیت دکتر",
    "بادکش",
    "حجامت",
    "فصد",
    "زالودرمانی",
]


# =========================================================
# Test Times
# =========================================================

TEST_TIMES = [
    "14:00",
    "15:00",
    "16:00",
    "17:00",
]


WORKING_WEEKDAYS = {
    5,  # Saturday
    6,  # Sunday
    0,  # Monday
    1,  # Tuesday
    2,  # Wednesday
    3,  # Thursday
}


# =========================================================
# Settings
# =========================================================

def seed_settings():

    for key, value in (
        DEFAULT_SETTINGS.items()
    ):

        if repository.get_setting(
            key
        ) is None:

            repository.set_setting(
                key,
                value,
            )


# =========================================================
# Services
# =========================================================

def seed_services():

    services = (
        repository.get_services()
    )

    by_name = {
        item["name"]: item
        for item in services
    }

    # -----------------------------------------------------
    # Migration from old version
    # -----------------------------------------------------

    old_service = (
        by_name.get(
            "خدمت عمومی"
        )
    )

    if (
        old_service
        and "ویزیت دکتر"
        not in by_name
    ):

        repository.update_service(
            old_service["id"],
            "ویزیت دکتر",
            1,
        )

        by_name[
            "ویزیت دکتر"
        ] = {
            **old_service,
            "name": "ویزیت دکتر",
        }

    # -----------------------------------------------------
    # Create missing services
    # -----------------------------------------------------

    for service_name in (
        REQUIRED_SERVICES
    ):

        if (
            service_name
            in by_name
        ):
            continue

        service_id = (
            repository.create_service(
                service_name
            )
        )

        by_name[
            service_name
        ] = {
            "id": service_id,
            "name": service_name,
        }


# =========================================================
# Test Slots
# =========================================================

def seed_test_slots_for_doctor(
    days=31,
):

    services = (
        repository.get_services()
    )

    doctor_service = next(
        (
            item
            for item in services
            if item["name"]
            == "ویزیت دکتر"
        ),
        None,
    )

    if doctor_service is None:
        return

    today = date.today()

    for offset in range(
        days
    ):

        current_date = (
            today
            + timedelta(
                days=offset
            )
        )

        # Friday excluded
        if (
            current_date.weekday()
            not in WORKING_WEEKDAYS
        ):
            continue

        appointment_date = (
            current_date.isoformat()
        )

        for gender in (
            "male",
            "female",
        ):

            for start_time in (
                TEST_TIMES
            ):

                existing = (
                    repository.get_slot(
                        service_id=doctor_service[
                            "id"
                        ],
                        appointment_date=appointment_date,
                        start_time=start_time,
                        gender=gender,
                    )
                )

                if existing:
                    continue

                repository.create_slot(
                    service_id=doctor_service[
                        "id"
                    ],
                    appointment_date=appointment_date,
                    start_time=start_time,
                    gender=gender,
                    capacity=1,
                )


# =========================================================
# Seed
# =========================================================

def seed(
    create_test_slots=True,
):

    seed_settings()

    seed_services()

    if create_test_slots:

        seed_test_slots_for_doctor()


if __name__ == "__main__":

    seed(
        create_test_slots=True
    )

    print(
        "Database seed completed successfully."
    )