from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sqlite3
import requests
from database.repository import repository
from database.migrations import run_migrations
from api import crud
from utils.helpers import to_date_label

run_migrations()

app = FastAPI(title="Clinic Dashboard API", version="3.8.5")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class StatusUpdate(BaseModel): status: str
class SettingUpdate(BaseModel): key: str; value: str
class LoginRequest(BaseModel): username: str; password: str
class CreatePatientRequest(BaseModel): first_name: str; last_name: str; national_id: str; phone_number: str; gender: str = "male"; insurance: str = "none"
class UpdatePatientRequest(BaseModel): first_name: str; last_name: str; phone_number: str; gender: str = "male"
class DeskBookRequest(BaseModel): national_id: str; first_name: Optional[str] = None; last_name: Optional[str] = None; phone_number: Optional[str] = None; patient_gender: Optional[str] = "male"; service_id: int; appointment_date: str; start_time: str; gender: str = "all"
class AppointmentCreateRequest(BaseModel): patient_id: int; service_id: int; appointment_date: str; start_time: str; gender: str = "all"
class ServiceCreateRequest(BaseModel): name: str; price: int = 0; has_gender: int = 0
class ServiceUpdateRequest(BaseModel): name: str; price: int; has_gender: int
class ToggleServiceRequest(BaseModel): is_active: int
class ScheduleConfigOverride(BaseModel): date: str; service_id: int; slots: List[Dict[str, str]]

def send_bale_notification(bale_user_id: int, message_text: str):
    token = os.getenv("BALE_TOKEN")
    if not token or not bale_user_id: return
    url = f"https://tapi.bale.ai/bot{token}/sendMessage"
    payload = {"chat_id": str(bale_user_id), "text": message_text}
    try: requests.post(url, json=payload, timeout=5)
    except Exception: pass

@app.get("/")
def health_check() -> dict: return {"status": "success", "message": "ای‌پی‌آی کلینیک فعال است"}

@app.post("/api/login")
def login(data: LoginRequest) -> dict:
    admin_user = os.getenv("ADMIN_USERNAME", "admin"); admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    sec_user = os.getenv("SECRETARY_USERNAME", "secretary"); sec_pass = os.getenv("SECRETARY_PASSWORD", "sec123")
    if data.username == admin_user and data.password == admin_pass: return {"success": True, "token": "clinic_secure_token_admin", "role": "admin", "name": "مدیر سیستم"}
    elif data.username == sec_user and data.password == sec_pass: return {"success": True, "token": "clinic_secure_token_secretary", "role": "secretary", "name": "منشی مطب"}
    raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور اشتباه است")

@app.post("/api/desk/book")
def desk_book(payload: DeskBookRequest) -> dict:
    try:
        patient = crud.get_patient_by_national_id(payload.national_id)
        if not patient:
            if not payload.first_name or not payload.phone_number: raise HTTPException(status_code=400, detail="اطلاعات بیمار برای ثبت جدید ناقص است.")
            try: patient_id = crud.create_patient_by_staff(payload.first_name, payload.last_name, payload.national_id, payload.phone_number, payload.patient_gender)
            except sqlite3.IntegrityError: raise HTTPException(status_code=400, detail="این کد ملی قبلاً ثبت شده است.")
        else: patient_id = patient["id"]
        appt_id = crud.create_appointment_by_staff(patient_id, payload.service_id, payload.appointment_date, payload.start_time, payload.gender, source="panel")
        return {"success": True, "appointment_id": appt_id}
    except HTTPException as http_exc: raise http_exc
    except Exception: raise HTTPException(status_code=500, detail="خطای سرور در ثبت اطلاعات.")

@app.get("/api/services")
def get_all_services() -> List[Dict[str, Any]]: return repository.get_services()

@app.get("/api/services/all")
def get_all_services_admin() -> List[Dict[str, Any]]: return crud.get_all_services_admin()

@app.post("/api/services")
def create_service(payload: ServiceCreateRequest) -> dict:
    try: return {"success": True, "service_id": crud.add_service(payload.name, payload.price, payload.has_gender)}
    except ValueError: raise HTTPException(status_code=400, detail="خدمتی با این نام قبلاً ثبت شده است.")

@app.put("/api/services/{service_id}")
def update_service(service_id: int, payload: ServiceUpdateRequest) -> dict:
    try:
        success = crud.update_service_info(service_id, payload.name, payload.price, payload.has_gender)
        if not success: raise HTTPException(status_code=404, detail="خدمت یافت نشد.")
        return {"success": True}
    except ValueError:
        raise HTTPException(status_code=400, detail="خدمتی با این نام قبلاً ثبت شده است.")

@app.delete("/api/services/{service_id}")
def delete_service(service_id: int) -> dict:
    success = crud.delete_service(service_id)
    if not success: raise HTTPException(status_code=404, detail="خدمت یافت نشد.")
    return {"success": True}

@app.put("/api/services/{service_id}/toggle")
def toggle_service(service_id: int, payload: ToggleServiceRequest) -> dict:
    success = crud.toggle_service_status(service_id, payload.is_active)
    if not success: raise HTTPException(status_code=404, detail="خدمت یافت نشد.")
    return {"success": True}

@app.get("/api/dashboard/stats")
def get_stats() -> dict: return crud.get_dashboard_stats()

@app.get("/api/reports/stats")
def get_reports_stats() -> dict: return crud.get_reports_stats()

@app.get("/api/dashboard/today")
def get_today_appointments() -> List[Dict[str, Any]]: return crud.get_todays_appointments()

@app.get("/api/patients")
def get_patients() -> List[Dict[str, Any]]: return crud.get_all_patients()

@app.get("/api/patients/search/{national_id}")
def search_patient(national_id: str) -> dict:
    patient = crud.get_patient_by_national_id(national_id)
    if not patient: raise HTTPException(status_code=404, detail="بیمار یافت نشد.")
    return patient

@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: int, payload: UpdatePatientRequest) -> dict:
    success = crud.update_patient_info(patient_id, payload.first_name, payload.last_name, payload.phone_number, payload.gender)
    if not success: raise HTTPException(status_code=404, detail="بیمار یافت نشد.")
    return {"success": True, "message": "بروزرسانی با موفقیت انجام شد."}

@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int) -> dict:
    success = crud.soft_delete_patient(patient_id)
    if not success: raise HTTPException(status_code=404, detail="بیمار یافت نشد.")
    return {"success": True, "message": "بیمار با موفقیت بایگانی شد."}

@app.post("/api/patients")
def create_patient(payload: CreatePatientRequest) -> dict:
    try: return {"success": True, "patient_id": crud.create_patient_by_staff(payload.first_name, payload.last_name, payload.national_id, payload.phone_number, payload.gender, payload.insurance)}
    except sqlite3.IntegrityError: raise HTTPException(status_code=400, detail="این کد ملی قبلاً ثبت شده است.")

@app.get("/api/appointments")
def get_appointments() -> List[Dict[str, Any]]: return crud.get_all_appointments()

@app.post("/api/appointments")
def create_appointment(payload: AppointmentCreateRequest) -> dict: return {"success": True, "appointment_id": crud.create_appointment_by_staff(payload.patient_id, payload.service_id, payload.appointment_date, payload.start_time, payload.gender, source="bot")}

@app.put("/api/appointments/{appointment_id}/status")
def update_status(appointment_id: int, payload: StatusUpdate, background_tasks: BackgroundTasks) -> dict:
    appt_info = crud.get_appointment_with_user_info(appointment_id)
    success = crud.update_appointment_status(appointment_id, payload.status)
    if not success: raise HTTPException(status_code=404, detail="نوبت یافت نشد.")
    if appt_info and appt_info.get("bale_user_id"):
        patient_name = f"{appt_info.get('first_name','')} {appt_info.get('last_name','')}"
        date_label = to_date_label(appt_info.get('appointment_date'))
        time_label = appt_info.get('start_time')
        service_name = appt_info.get('service_name', 'خدمت')
        msg = ""
        if payload.status == "cancelled":
            msg = f"❌ کاربر گرامی، نوبت مربوط به «{patient_name}» برای خدمت «{service_name}» در تاریخ {date_label} ساعت {time_label} توسط کلینیک لغو گردید.\nجهت کسب اطلاعات بیشتر یا رزرو مجدد لطفاً با مطب تماس بگیرید."
        elif payload.status == "accepted":
            msg = f"✅ کاربر گرامی، نوبت مربوط به «{patient_name}» برای خدمت «{service_name}» در تاریخ {date_label} ساعت {time_label} با موفقیت پذیرش شد.\nبا آرزوی سلامتی برای شما."
        if msg: background_tasks.add_task(send_bale_notification, appt_info["bale_user_id"], msg)
    return {"success": True, "message": "وضعیت با موفقیت تغییر کرد."}

@app.get("/api/settings")
def get_settings() -> dict: return crud.get_general_settings()

@app.post("/api/settings")
def update_setting(payload: SettingUpdate) -> dict: 
    crud.save_general_setting(payload.key, payload.value)
    return {"success": True}

@app.get("/api/settings/schedule")
def get_schedule() -> dict: return crud.get_schedule_config()

@app.post("/api/settings/schedule")
def save_schedule(payload: Dict[str, Any]) -> dict: crud.save_schedule_config(payload); return {"success": True}

@app.get("/api/schedule/slots")
def get_slots(date: str, service_id: int) -> List[Dict[str, Any]]: return crud.get_date_slots(date, service_id)

@app.post("/api/schedule/override")
def override_slots(payload: ScheduleConfigOverride, background_tasks: BackgroundTasks) -> dict:
    cancelled_bale_ids = crud.override_date_slots(payload.date, payload.service_id, payload.slots)
    for bale_id in cancelled_bale_ids:
        msg = f"⚠️ کاربر گرامی، به دلیل تغییرات در زمان‌بندی پزشک، نوبت شما در تاریخ {to_date_label(payload.date)} لغو گردید. لطفاً مجدداً برای دریافت نوبت اقدام نمایید."
        background_tasks.add_task(send_bale_notification, bale_id, msg)
    return {"success": True}

@app.get("/api/schedule/overrides/list")
def list_overrides() -> Dict[str, Any]: return crud.get_overridden_dates()

@app.delete("/api/schedule/override")
def reset_override(date: str, service_id: int) -> dict:
    crud.reset_override(date, service_id)
    return {"success": True}