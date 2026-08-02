# models/appointment.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Appointment:

    id: int

    patient_id: int

    service_id: int

    appointment_date: str

    start_time: str

    end_time: str

    gender: str

    status: str = "scheduled"

    reason: Optional[str] = None

    notes: Optional[str] = None

    created_by: Optional[int] = None

    created_at: Optional[str] = None

    updated_at: Optional[str] = None

    service_name: Optional[str] = None

    patient_first_name: Optional[str] = None

    patient_last_name: Optional[str] = None

    patient_phone: Optional[str] = None

    patient_national_id: Optional[str] = None

    patient_birth_date: Optional[str] = None

    patient_gender: Optional[str] = None

    patient_insurance: Optional[str] = None