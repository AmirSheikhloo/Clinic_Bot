# services/appointment_service.py

from typing import List, Optional

from database.repository import repository
from models.appointment import Appointment


class AppointmentService:

    # =========================================================
    # Internal Mapper
    # =========================================================

    @staticmethod
    def _to_appointment(
        data: Optional[dict],
    ) -> Optional[Appointment]:

        if not data:
            return None

        allowed_fields = {
            "id",
            "patient_id",
            "service_id",
            "appointment_date",
            "start_time",
            "end_time",
            "gender",
            "status",
            "reason",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
            "service_name",
            "patient_first_name",
            "patient_last_name",
            "patient_phone",
            "patient_national_id",
            "patient_birth_date",
            "patient_gender",
            "patient_insurance",
        }

        values = {
            key: value
            for key, value in data.items()
            if key in allowed_fields
        }

        return Appointment(
            **values
        )

    # =========================================================
    # Create
    # =========================================================

    def create_appointment(
        self,
        patient_id: int,
        service_id: int,
        appointment_date: str,
        start_time: str,
        end_time: str,
        gender: str,
        status: str = "scheduled",
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Optional[Appointment]:

        appointment_id = (
            repository.create_appointment_if_available(
                patient_id=patient_id,
                service_id=service_id,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                gender=gender,
                status=status,
                reason=reason,
                notes=notes,
                created_by=created_by,
            )
        )

        if appointment_id is None:
            return None

        return self.get_appointment(
            appointment_id
        )

    # =========================================================
    # Get
    # =========================================================

    def get_appointment(
        self,
        appointment_id: int,
    ) -> Optional[Appointment]:

        data = repository.get_appointment_by_id(
            appointment_id
        )

        return self._to_appointment(
            data
        )

    # =========================================================
    # Patient Appointments
    # =========================================================

    def get_patient_appointments(
        self,
        patient_id: int,
    ) -> List[Appointment]:

        records = repository.get_patient_appointments(
            patient_id=patient_id,
        )

        return [
            self._to_appointment(record)
            for record in records
            if self._to_appointment(record)
            is not None
        ]

    # =========================================================
    # Active Appointment
    # =========================================================

    def get_active_appointment(
        self,
        service_id: int,
        appointment_date: str,
        start_time: str,
        gender: str,
    ) -> Optional[Appointment]:

        data = repository.get_active_appointment(
            service_id=service_id,
            appointment_date=appointment_date,
            start_time=start_time,
            gender=gender,
        )

        return self._to_appointment(
            data
        )

    # =========================================================
    # Confirm
    # =========================================================

    def confirm_appointment(
        self,
        appointment_id: int,
    ) -> Optional[Appointment]:

        appointment = self.get_appointment(
            appointment_id
        )

        if appointment is None:
            return None

        if appointment.status != "scheduled":
            return appointment

        repository.update_appointment_status(
            appointment_id=appointment_id,
            status="scheduled",
        )

        return self.get_appointment(
            appointment_id
        )

    # =========================================================
    # Cancel
    # =========================================================

    def cancel_appointment(
        self,
        appointment_id: int,
    ) -> Optional[Appointment]:

        appointment = self.get_appointment(
            appointment_id
        )

        if appointment is None:
            return None

        if appointment.status in (
            "cancelled",
            "completed",
            "no_show",
        ):
            return appointment

        repository.update_appointment_status(
            appointment_id=appointment_id,
            status="cancelled",
        )

        return self.get_appointment(
            appointment_id
        )

    # =========================================================
    # Complete
    # =========================================================

    def complete_appointment(
        self,
        appointment_id: int,
    ) -> Optional[Appointment]:

        appointment = self.get_appointment(
            appointment_id
        )

        if appointment is None:
            return None

        if appointment.status in (
            "cancelled",
            "completed",
            "no_show",
        ):
            return appointment

        repository.update_appointment_status(
            appointment_id=appointment_id,
            status="completed",
        )

        return self.get_appointment(
            appointment_id
        )

    # =========================================================
    # No Show
    # =========================================================

    def mark_no_show(
        self,
        appointment_id: int,
    ) -> Optional[Appointment]:

        appointment = self.get_appointment(
            appointment_id
        )

        if appointment is None:
            return None

        if appointment.status in (
            "cancelled",
            "completed",
            "no_show",
        ):
            return appointment

        repository.update_appointment_status(
            appointment_id=appointment_id,
            status="no_show",
        )

        return self.get_appointment(
            appointment_id
        )


appointment_service = AppointmentService()