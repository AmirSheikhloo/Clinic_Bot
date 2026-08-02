# services/patient_service.py

from typing import Any, Optional

from database.repository import repository
from models.patient import Patient


class PatientService:

    # =========================================================
    # Internal Mapper
    # =========================================================

    @staticmethod
    def _to_patient(
        data: Optional[dict],
    ) -> Optional[Patient]:

        if not data:
            return None

        return Patient(
            id=data.get("id"),
            user_id=data.get("user_id"),
            national_id=data.get("national_id"),
            first_name=data.get(
                "first_name",
                "",
            ),
            last_name=data.get(
                "last_name",
                "",
            ),
            phone=data.get(
                "phone",
                data.get(
                    "phone_number",
                    "",
                ),
            ),
            birth_date=data.get(
                "birth_date"
            ),
            gender=data.get(
                "gender"
            ),
            insurance=data.get(
                "insurance"
            ),
            address=data.get(
                "address"
            ),
            created_at=data.get(
                "created_at"
            ),
            updated_at=data.get(
                "updated_at"
            ),
        )

    # =========================================================
    # Create
    # =========================================================

    def create_patient(
        self,
        user_id: Optional[int],
        first_name: str,
        last_name: str,
        phone: str,
        national_id: Optional[str] = None,
        birth_date: Optional[str] = None,
        gender: Optional[str] = None,
        insurance: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Optional[Patient]:

        patient_id = repository.create_patient(
            user_id=user_id,
            national_id=national_id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            birth_date=birth_date,
            gender=gender,
            insurance=insurance,
            address=address,
        )

        return self.get_patient(
            patient_id
        )

    # =========================================================
    # Get
    # =========================================================

    def get_patient(
        self,
        patient_id: int,
    ) -> Optional[Patient]:

        data = repository.get_patient_by_id(
            patient_id
        )

        return self._to_patient(
            data
        )

    # =========================================================
    # Get By User
    # =========================================================

    def get_patient_by_user_id(
        self,
        user_id: int,
    ) -> Optional[Patient]:

        data = repository.get_patient_by_user_id(
            user_id
        )

        return self._to_patient(
            data
        )

    # =========================================================
    # Get By National ID
    # =========================================================

    def get_patient_by_national_id(
        self,
        national_id: str,
    ) -> Optional[Patient]:

        data = repository.get_patient_by_national_id(
            national_id
        )

        return self._to_patient(
            data
        )

    # =========================================================
    # Update
    # =========================================================

    def update_patient(
        self,
        patient_id: int,
        **fields: Any,
    ) -> Optional[Patient]:

        current = repository.get_patient_by_id(
            patient_id
        )

        if current is None:
            return None

        first_name = fields.get(
            "first_name",
            current.get("first_name", ""),
        )

        last_name = fields.get(
            "last_name",
            current.get("last_name", ""),
        )

        phone = fields.get(
            "phone",
            fields.get(
                "phone_number",
                current.get(
                    "phone_number",
                    "",
                ),
            ),
        )

        birth_date = fields.get(
            "birth_date",
            current.get("birth_date"),
        )

        gender = fields.get(
            "gender",
            current.get("gender"),
        )

        insurance = fields.get(
            "insurance",
            current.get("insurance"),
        )

        address = fields.get(
            "address",
            current.get("address"),
        )

        repository.update_patient(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            birth_date=birth_date,
            gender=gender,
            insurance=insurance,
            address=address,
        )

        return self.get_patient(
            patient_id
        )

    # =========================================================
    # Delete
    # =========================================================

    def delete_patient(
        self,
        patient_id: int,
    ) -> bool:

        patient = repository.get_patient_by_id(
            patient_id
        )

        if patient is None:
            return False

        try:
            repository.delete_appointment_by_patient(
                patient_id
            )

            repository.delete_patient(
                patient_id
            )

            return True

        except Exception:
            return False


patient_service = PatientService()