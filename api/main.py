from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sqlite3
from database.repository import repository
from database.migrations import run_migrations
from api import crud

run_migrations()

app = FastAPI(
    title="Clinic Dashboard API",
    version="2.8.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusUpdate(BaseModel):
    status: str

class SettingUpdate(BaseModel):
    key: str
    value: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreatePatientRequest(BaseModel):
    first_name: str
    last_name: str
    national_id: str
    phone_number: str
    gender: str = "male"
    insurance: str = "none"

class UpdatePatientRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    gender: str = "male"

class DeskBookRequest(BaseModel):
    national_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    patient_gender: Optional[str] = "male"
    service_id: int
    appointment_date: str
    start_time: str
    gender: str = "all"

class AppointmentCreateRequest(BaseModel):
    patient_id: int
    service_id: int
    appointment_date: str
    start_time: str
    gender: str = "all"

class ServiceCreateRequest(BaseModel):
    name: str
    price: int = 0

@app.get("/")
def health_check() -> dict:
    return {"status": "success", "message": "ای‌پی‌آی کلینیک فعال است"}

@app.post("/api/login")
def login(data: LoginRequest) -> dict:
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
    sec_user = os.getenv("SECRETARY_USERNAME", "secretary")
    sec_pass = os.getenv("SECRETARY_PASSWORD", "sec123")
    
    if data.username == admin_user and data.password == admin_pass:
        return {"success": True, "token": "clinic_secure_token_admin", "role": "admin", "name": "مدیر سیستم"}
    elif data.username == sec_user and data.password == sec_pass:
        return {"success": True, "token": "clinic_secure_token_secretary", "role": "secretary", "name": "منشی مطب"}
        
    raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور اشتباه است")

@app.post("/api/desk/book")
def desk_book(payload: DeskBookRequest) -> dict:
    try:
        patient = crud.get_patient_by_national_id(payload.national_id)
        if not patient:
            if not payload.first_name or not payload.phone_number:
                raise HTTPException(status_code=400, detail="اطلاعات بیمار برای ثبت جدید ناقص است.")
            try:
                patient_id = crud.create_patient_by_staff(
                    payload.first_name, payload.last_name, payload.national_id, payload.phone_number, payload.patient_gender
                )
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="این کد ملی قبلاً برای شخص دیگری در سیستم ثبت شده است.")
        else:
            patient_id = patient["id"]

        appt_id = crud.create_appointment_by_staff(
            patient_id, payload.service_id, payload.appointment_date, payload.start_time, payload.gender, source="panel"
        )
        return {"success": True, "appointment_id": appt_id}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        raise HTTPException(status_code=500, detail="خطای سرور در ثبت اطلاعات.")

@app.get("/api/services")
def get_all_services() -> List[Dict[str, Any]]:
    try:
        return repository.get_services()
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در دریافت لیست خدمات.")

@app.post("/api/services")
def create_service(payload: ServiceCreateRequest) -> dict:
    try:
        service_id = crud.add_service(payload.name, payload.price)
        return {"success": True, "service_id": service_id}
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در ایجاد خدمت جدید.")

@app.get("/api/dashboard/stats")
def get_stats() -> dict:
    try:
        return crud.get_dashboard_stats()
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در دریافت آمار داشبورد.")

@app.get("/api/patients")
def get_patients() -> List[Dict[str, Any]]:
    try:
        return crud.get_all_patients()
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در دریافت لیست بیماران.")

@app.get("/api/patients/search/{national_id}")
def search_patient(national_id: str) -> dict:
    patient = crud.get_patient_by_national_id(national_id)
    if not patient:
        raise HTTPException(status_code=404, detail="بیمار یافت نشد.")
    return patient

@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: int, payload: UpdatePatientRequest) -> dict:
    try:
        success = crud.update_patient_info(patient_id, payload.first_name, payload.last_name, payload.phone_number, payload.gender)
        if not success:
            raise HTTPException(status_code=404, detail="بیمار مورد نظر یافت نشد.")
        return {"success": True, "message": "بروزرسانی با موفقیت انجام شد."}
    except sqlite3.IntegrityError:
        # در این آپدیت کد ملی تغییر نمی‌کند پس ارور یکتایی معمولاً رخ نمی‌دهد
        raise HTTPException(status_code=400, detail="خطای یکتایی اطلاعات در پایگاه داده.")
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در بروزرسانی اطلاعات بیمار.")

@app.post("/api/patients")
def create_patient(payload: CreatePatientRequest) -> dict:
    try:
        patient_id = crud.create_patient_by_staff(
            payload.first_name, payload.last_name, payload.national_id,
            payload.phone_number, payload.gender, payload.insurance
        )
        return {"success": True, "patient_id": patient_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="این کد ملی قبلاً برای شخص دیگری در سیستم ثبت شده است.")
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در ثبت بیمار جدید.")

@app.get("/api/appointments")
def get_appointments() -> List[Dict[str, Any]]:
    try:
        return crud.get_all_appointments()
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در دریافت لیست نوبت‌ها.")

@app.post("/api/appointments")
def create_appointment(payload: AppointmentCreateRequest) -> dict:
    try:
        appt_id = crud.create_appointment_by_staff(
            payload.patient_id, payload.service_id, payload.appointment_date, payload.start_time, payload.gender, source="bot"
        )
        return {"success": True, "appointment_id": appt_id}
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در ایجاد نوبت جدید.")

@app.put("/api/appointments/{appointment_id}/status")
def update_status(appointment_id: int, payload: StatusUpdate) -> dict:
    try:
        success = crud.update_appointment_status(appointment_id, payload.status)
        if not success:
            raise HTTPException(status_code=404, detail="نوبت یافت نشد.")
        return {"success": True, "message": "وضعیت با موفقیت تغییر کرد."}
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در تغییر وضعیت نوبت.")

@app.get("/api/settings")
def get_settings() -> dict:
    try:
        return {
            "clinic_name": repository.get_setting("clinic_name", ""),
            "clinic_phone": repository.get_setting("clinic_phone", ""),
            "clinic_address": repository.get_setting("clinic_address", ""),
            "working_hours": repository.get_setting("working_hours", "")
        }
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در دریافت تنظیمات.")

@app.post("/api/settings")
def update_setting(payload: SettingUpdate) -> dict:
    try:
        repository.set_setting(payload.key, payload.value)
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در ذخیره تنظیمات.")