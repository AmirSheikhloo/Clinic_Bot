from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from database.repository import repository
from database.migrations import run_migrations
from api import crud

run_migrations()

app = FastAPI(
    title="Clinic Dashboard API",
    version="2.0.0"
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

class ServiceCreateRequest(BaseModel):
    name: str
    price: int = 0

@app.get("/")
def health_check() -> dict:
    return {
        "status": "success",
        "message": "Clinic API v2.0 is active"
    }

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

@app.get("/api/services")
def get_all_services() -> List[Dict[str, Any]]:
    try:
        return repository.get_services()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/services")
def create_service(payload: ServiceCreateRequest) -> dict:
    try:
        service_id = crud.add_service(payload.name, payload.price)
        return {"success": True, "service_id": service_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Error creating service")

@app.get("/api/dashboard/stats")
def get_stats() -> dict:
    try:
        return crud.get_dashboard_stats()
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching stats")

@app.get("/api/patients")
def get_patients() -> List[Dict[str, Any]]:
    try:
        return crud.get_all_patients()
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching patients")

@app.post("/api/patients")
def create_patient(payload: CreatePatientRequest) -> dict:
    try:
        patient_id = crud.create_patient_by_staff(
            payload.first_name, payload.last_name, payload.national_id,
            payload.phone_number, payload.gender, payload.insurance
        )
        return {"success": True, "patient_id": patient_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Error creating patient")

@app.get("/api/appointments")
def get_appointments() -> List[Dict[str, Any]]:
    try:
        return crud.get_all_appointments()
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching appointments")

@app.put("/api/appointments/{appointment_id}/status")
def update_status(appointment_id: int, payload: StatusUpdate) -> dict:
    try:
        success = crud.update_appointment_status(appointment_id, payload.status)
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"success": True, "message": "Status updated successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating status")

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
        raise HTTPException(status_code=500, detail="Error fetching settings")

@app.post("/api/settings")
def update_setting(payload: SettingUpdate) -> dict:
    try:
        repository.set_setting(payload.key, payload.value)
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=500, detail="Error updating settings")