# models/patient.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Patient:

    id: Optional[int] = None

    user_id: Optional[int] = None

    national_id: Optional[str] = None

    first_name: str = ""

    last_name: str = ""

    phone: str = ""

    birth_date: Optional[str] = None

    gender: Optional[str] = None

    insurance: Optional[str] = None

    address: Optional[str] = None

    created_at: Optional[datetime | str] = None

    updated_at: Optional[datetime | str] = None

    @property
    def full_name(self) -> str:
        return (
            f"{self.first_name} "
            f"{self.last_name}"
        ).strip()