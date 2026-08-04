from datetime import date, timedelta
from typing import Optional
from database.repository import repository

WORKING_WEEKDAYS = {5, 6, 0, 1, 2, 3}

class ScheduleService:
    @staticmethod
    def is_friday(appointment_date: str) -> bool:
        try:
            return date.fromisoformat(appointment_date).weekday() == 4
        except (TypeError, ValueError):
            return False

    def get_services(self, gender: Optional[str] = None, days_ahead: int = 7) -> list[dict]:
        return repository.get_services()

    def get_service_dates(self, service_id: int, gender: str, days_ahead: int = 7) -> list[str]:
        today = date.today()
        result = []
        for offset in range(1, days_ahead + 1):
            current_date = today + timedelta(days=offset)
            if current_date.weekday() not in WORKING_WEEKDAYS:
                continue
            result.append(current_date.isoformat())
        return result

    def get_available_dates(self, service_id: int, gender: str, days_ahead: int = 7) -> list[str]:
        return self.get_service_dates(service_id=service_id, gender=gender, days_ahead=days_ahead)

    def get_times(self, service_id: int, appointment_date: str, gender: str) -> list[dict]:
        if self.is_friday(appointment_date):
            return []
        
        # این خط مستقیماً زمان‌های مربوط به جنسیت را از دیتابیس می‌گیرد و مشکلِ فیلترینگ اشتباه کاملا برطرف شده است
        return repository.get_available_times(service_id=service_id, appointment_date=appointment_date, gender=gender)

    def get_available_times(self, service_id: int, appointment_date: str, gender: str) -> list[dict]:
        return self.get_times(service_id=service_id, appointment_date=appointment_date, gender=gender)

    def is_slot_available(self, service_id: int, appointment_date: str, start_time: str, gender: str) -> bool:
        if self.is_friday(appointment_date):
            return False
        times = self.get_times(service_id=service_id, appointment_date=appointment_date, gender=gender)
        for item in times:
            if str(item.get("start_time")) != str(start_time):
                continue
            # بررسی پر شدن ظرفیت
            return int(item.get("booked_count", 0) or 0) < int(item.get("capacity", 1) or 1)
        return False

schedule_service = ScheduleService()