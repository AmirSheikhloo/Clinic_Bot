from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from database.repository import repository
from api import crud

app = FastAPI(
    title="Clinic Dashboard API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check() -> dict:
    return {
        "status": "success",
        "message": "Clinic API is active"
    }

@app.get("/api/services")
def get_all_services() -> List[Dict[str, Any]]:
    try:
        return repository.get_services()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats")
def get_stats() -> dict:
    try:
        return crud.get_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patients")
def get_patients() -> List[Dict[str, Any]]:
    try:
        return crud.get_all_patients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/appointments")
def get_appointments() -> List[Dict[str, Any]]:
    try:
        return crud.get_all_appointments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))