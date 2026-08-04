from datetime import date, timedelta
from database.repository import repository

DEFAULT_SETTINGS = {
    "clinic_name": "درمانگاه طب سنتی دکتر ولی‌الله گرایلی ملک",
    "clinic_phone": "02146292250 یا 02144386143",
    "clinic_address": "تهران، بزرگراه اشرفی اصفهانی، بالاتر از سه راه مرزداران، کوچه شهید ماشاالله ردایی، طبقه دوم مسجد حضرت ابوالفضل (دارالشفای حضرت ابوالفضل)",
    "working_days": "Saturday,Sunday,Monday,Tuesday,Wednesday,Thursday",
    "working_hours": "همه‌روزه به جز جمعه‌ها",
    "timezone": "Asia/Tehran",
    "appointment_duration": "30",
}

REQUIRED_SERVICES = [
    "ویزیت دکتر گرایلی",
    "غمز و رگ گیری",
    "طب سوزنی",
    "فصد",
    "اسکن کل بدن",
    "سم زدایی",
    "امبدینگ(لاغری)",
    "بادکش",
    "حجامت عام",
    "زالودرمانی",
]

TEST_TIMES = ["14:00", "15:00", "16:00", "17:00"]
WORKING_WEEKDAYS = {5, 6, 0, 1, 2, 3}

def seed_settings():
    for key, value in DEFAULT_SETTINGS.items():
        if repository.get_setting(key) is None:
            repository.set_setting(key, value)

def seed_services():
    services = repository.get_services()
    by_name = {item["name"]: item for item in services}

    old_service = by_name.get("خدمت عمومی")
    if old_service and "ویزیت دکتر گرایلی" not in by_name:
        repository.update_service(old_service["id"], "ویزیت دکتر گرایلی", 1)
        by_name["ویزیت دکتر گرایلی"] = {**old_service, "name": "ویزیت دکتر گرایلی"}

    for service_name in REQUIRED_SERVICES:
        if service_name in by_name: continue
        service_id = repository.create_service(service_name)
        by_name[service_name] = {"id": service_id, "name": service_name}

def seed_test_slots_for_all_services(days=31):
    services = repository.get_services()
    today = date.today()
    
    for service in services:
        is_gendered = service["name"] in ["بادکش", "حجامت عام", "زالودرمانی"]
        genders = ["male", "female"] if is_gendered else ["all"]
        
        for offset in range(days):
            current_date = today + timedelta(days=offset)
            if current_date.weekday() not in WORKING_WEEKDAYS: continue
            appointment_date = current_date.isoformat()
            
            for gender in genders:
                for start_time in TEST_TIMES:
                    existing = repository.get_slot(service_id=service["id"], appointment_date=appointment_date, start_time=start_time, gender=gender)
                    if existing: continue
                    repository.create_slot(service_id=service["id"], appointment_date=appointment_date, start_time=start_time, gender=gender, capacity=1)

def seed(create_test_slots=True):
    seed_settings()
    seed_services()
    if create_test_slots:
        seed_test_slots_for_all_services()

if __name__ == "__main__":
    seed(create_test_slots=True)
    print("Database seed completed successfully.")