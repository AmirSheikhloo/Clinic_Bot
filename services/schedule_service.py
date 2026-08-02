from datetime import date, timedelta
from typing import Optional

from database.repository import repository


# =========================================================
# Working Days
# =========================================================

WORKING_WEEKDAYS = {
    5,  # Saturday
    6,  # Sunday
    0,  # Monday
    1,  # Tuesday
    2,  # Wednesday
    3,  # Thursday
}


class ScheduleService:

    # =========================================================
    # Friday
    # =========================================================

    @staticmethod
    def is_friday(
        appointment_date: str,
    ) -> bool:

        try:

            return (
                date.fromisoformat(
                    appointment_date
                ).weekday()
                == 4
            )

        except (
            TypeError,
            ValueError,
        ):

            return False

    # =========================================================
    # Merge Times
    # =========================================================

    @staticmethod
    def _merge_times(
        *groups,
    ):

        merged = {}

        for group in groups:

            for item in group or []:

                start_time = (
                    item.get("start_time")
                    or item.get("time")
                )

                if not start_time:
                    continue

                key = str(
                    start_time
                )

                if key not in merged:

                    merged[key] = {
                        "start_time": key,
                        "appointment_date":
                            item.get(
                                "appointment_date"
                            ),
                        "service_id":
                            item.get(
                                "service_id"
                            ),
                        "capacity": int(
                            item.get(
                                "capacity",
                                1,
                            )
                            or 1
                        ),
                        "booked_count": int(
                            item.get(
                                "booked_count",
                                0,
                            )
                            or 0
                        ),
                    }

                else:

                    merged[key][
                        "capacity"
                    ] += int(
                        item.get(
                            "capacity",
                            1,
                        )
                        or 1
                    )

                    merged[key][
                        "booked_count"
                    ] += int(
                        item.get(
                            "booked_count",
                            0,
                        )
                        or 0
                    )

        result = list(
            merged.values()
        )

        result.sort(
            key=lambda item:
            item["start_time"]
        )

        for item in result:

            item["available"] = (
                item["booked_count"]
                <
                item["capacity"]
            )

        return result

    # =========================================================
    # Services
    # =========================================================

    def get_services(
        self,
        gender: Optional[str] = None,
        days_ahead: int = 7,
    ) -> list[dict]:

        # همه خدمات فعال را برمی‌گردانیم.
        # پر بودن تاریخ باعث حذف شدن خود خدمت نمی‌شود.

        return repository.get_services()

    # =========================================================
    # Dates
    # =========================================================

    def get_service_dates(
        self,
        service_id: int,
        gender: str,
        days_ahead: int = 7,
    ) -> list[str]:

        today = date.today()

        result = []

        for offset in range(
            1,
            days_ahead + 1,
        ):

            current_date = (
                today
                + timedelta(
                    days=offset
                )
            )

            # جمعه تعطیل است.
            if (
                current_date.weekday()
                not in WORKING_WEEKDAYS
            ):
                continue

            result.append(
                current_date.isoformat()
            )

        return result

    def get_available_dates(
        self,
        service_id: int,
        gender: str,
        days_ahead: int = 7,
    ) -> list[str]:

        return self.get_service_dates(
            service_id=service_id,
            gender=gender,
            days_ahead=days_ahead,
        )

    # =========================================================
    # Times
    # =========================================================

    def get_times(
        self,
        service_id: int,
        appointment_date: str,
        gender: str,
    ) -> list[dict]:

        if self.is_friday(
            appointment_date
        ):
            return []

        # برای ویزیت دکتر جنسیت در
        # مرحله انتخاب خدمت پرسیده نمی‌شود.
        #
        # بنابراین slotهای آقا و خانم
        # با هم بررسی می‌شوند.

        if gender == "all":

            male_times = (
                repository.get_available_times(
                    service_id=service_id,
                    appointment_date=appointment_date,
                    gender="male",
                )
            )

            female_times = (
                repository.get_available_times(
                    service_id=service_id,
                    appointment_date=appointment_date,
                    gender="female",
                )
            )

            return self._merge_times(
                male_times,
                female_times,
            )

        if gender not in (
            "male",
            "female",
        ):
            return []

        return repository.get_available_times(
            service_id=service_id,
            appointment_date=appointment_date,
            gender=gender,
        )

    def get_available_times(
        self,
        service_id: int,
        appointment_date: str,
        gender: str,
    ) -> list[dict]:

        return self.get_times(
            service_id=service_id,
            appointment_date=appointment_date,
            gender=gender,
        )

    # =========================================================
    # Slot Availability
    # =========================================================

    def is_slot_available(
        self,
        service_id: int,
        appointment_date: str,
        start_time: str,
        gender: str,
    ) -> bool:

        if self.is_friday(
            appointment_date
        ):
            return False

        times = self.get_times(
            service_id=service_id,
            appointment_date=appointment_date,
            gender=gender,
        )

        for item in times:

            if (
                str(
                    item.get(
                        "start_time"
                    )
                )
                != str(start_time)
            ):
                continue

            return (
                int(
                    item.get(
                        "booked_count",
                        0,
                    )
                    or 0
                )
                <
                int(
                    item.get(
                        "capacity",
                        1,
                    )
                    or 1
                )
            )

        return False

    # =========================================================
    # Create Slot
    # =========================================================

    def create_slot(
        self,
        service_id: int,
        appointment_date: str,
        start_time: str,
        gender: str,
        capacity: int,
    ) -> int:

        if self.is_friday(
            appointment_date
        ):
            raise ValueError(
                "Friday is a holiday."
            )

        return repository.create_slot(
            service_id=service_id,
            appointment_date=appointment_date,
            start_time=start_time,
            gender=gender,
            capacity=capacity,
        )

    # =========================================================
    # Get Slot
    # =========================================================

    def get_slot(
        self,
        service_id: int,
        appointment_date: str,
        start_time: str,
        gender: str,
    ):

        if self.is_friday(
            appointment_date
        ):
            return None

        return repository.get_slot(
            service_id=service_id,
            appointment_date=appointment_date,
            start_time=start_time,
            gender=gender,
        )


schedule_service = ScheduleService()