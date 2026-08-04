from typing import Any, Optional
from database.connection import get_connection

class Repository:
    def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> int:
        with get_connection() as connection:
            cursor = connection.execute(query, parameters)
            connection.commit()
            return cursor.lastrowid

    def fetch_one(self, query: str, parameters: tuple[Any, ...] = ()) -> Optional[dict]:
        with get_connection() as connection:
            cursor = connection.execute(query, parameters)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, parameters: tuple[Any, ...] = ()) -> list[dict]:
        with get_connection() as connection:
            cursor = connection.execute(query, parameters)
            return [dict(row) for row in cursor.fetchall()]

    def create_user(self, bale_user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None, phone_number: Optional[str] = None, role: str = "patient") -> int:
        existing = self.get_user_by_bale_id(bale_user_id)
        if existing: return existing["id"]
        return self.execute("INSERT INTO users (bale_user_id, username, first_name, last_name, phone_number, role) VALUES (?, ?, ?, ?, ?, ?)", (bale_user_id, username, first_name, last_name, phone_number, role))

    def get_user_by_bale_id(self, bale_user_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM users WHERE bale_user_id = ?", (bale_user_id,))

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def update_user_phone(self, bale_user_id: int, phone_number: str) -> None:
        self.execute("UPDATE users SET phone_number = ?, updated_at = CURRENT_TIMESTAMP WHERE bale_user_id = ?", (phone_number, bale_user_id))

    def create_patient(self, user_id: Optional[int], first_name: str, last_name: str, phone: Optional[str] = None, phone_number: Optional[str] = None, national_id: Optional[str] = None, birth_date: Optional[str] = None, gender: Optional[str] = None, insurance: Optional[str] = None, address: Optional[str] = None) -> int:
        final_phone = phone_number if phone_number is not None else phone
        if not final_phone: raise ValueError("Patient phone number is required.")
        existing = None
        if national_id: existing = self.get_patient_by_national_id(national_id)
        if existing: 
            # در صورتی که بیمار وجود دارد اما به این یوزر متصل نیست، متصلش کن
            if user_id is not None: self.add_patient_profile(user_id, existing["id"])
            return existing["id"]
        patient_id = self.execute("INSERT INTO patients (user_id, national_id, first_name, last_name, phone_number, birth_date, gender, insurance, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, national_id, first_name, last_name, final_phone, birth_date, gender, insurance, address))
        if user_id is not None: self.add_patient_profile(user_id, patient_id)
        return patient_id

    def get_patient(self, patient_id: int) -> Optional[dict]:
        return self.get_patient_by_id(patient_id)

    def get_patient_by_id(self, patient_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM patients WHERE id = ?", (patient_id,))

    def get_patient_by_user_id(self, user_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM patients WHERE user_id = ? ORDER BY id LIMIT 1", (user_id,))

    def get_patient_by_national_id(self, national_id: str) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM patients WHERE national_id = ?", (national_id,))

    def get_all_patients(self) -> list[dict]:
        return self.fetch_all("SELECT * FROM patients ORDER BY first_name, last_name")

    def update_patient(self, patient_id: int, fields: Optional[dict] = None, **kwargs) -> bool:
        if fields is None: fields = {}
        fields = {**fields, **kwargs}
        allowed = {"user_id", "national_id", "first_name", "last_name", "phone", "phone_number", "birth_date", "gender", "insurance", "address"}
        values = {k: v for k, v in fields.items() if k in allowed}
        if "phone" in values: values["phone_number"] = values.pop("phone")
        if not values: return False
        assignments = ", ".join(f"{k} = ?" for k in values)
        parameters = tuple(values.values()) + (patient_id,)
        with get_connection() as connection:
            cursor = connection.execute(f"UPDATE patients SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", parameters)
            connection.commit()
            return cursor.rowcount > 0

    def add_patient_profile(self, user_id: int, patient_id: int) -> bool:
        with get_connection() as connection:
            connection.execute("INSERT OR IGNORE INTO user_patient_profiles (user_id, patient_id) VALUES (?, ?)", (user_id, patient_id))
            connection.commit()
        return True

    def get_patient_profiles(self, user_id: int) -> list[dict]:
        return self.fetch_all("SELECT p.* FROM patients p INNER JOIN user_patient_profiles upp ON upp.patient_id = p.id WHERE upp.user_id = ? ORDER BY p.id", (user_id,))

    def get_patient_profile(self, user_id: int, patient_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT p.* FROM patients p INNER JOIN user_patient_profiles upp ON upp.patient_id = p.id WHERE upp.user_id = ? AND upp.patient_id = ?", (user_id, patient_id))

    def create_service(self, name: str) -> int:
        existing = self.fetch_one("SELECT id FROM services WHERE name = ?", (name,))
        if existing: return existing["id"]
        return self.execute("INSERT INTO services (name) VALUES (?)", (name,))

    def get_service_by_id(self, service_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM services WHERE id = ? AND is_active = 1", (service_id,))

    def get_services(self) -> list[dict]:
        return self.fetch_all("SELECT * FROM services WHERE is_active = 1 ORDER BY id")

    def create_slot(self, service_id: int, appointment_date: str, start_time: str, gender: str, capacity: int, end_time: Optional[str] = None) -> int:
        existing = self.get_slot(service_id=service_id, appointment_date=appointment_date, start_time=start_time, gender=gender)
        if existing:
            self.execute("UPDATE appointment_slots SET capacity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (capacity, existing["id"]))
            return existing["id"]
        return self.execute("INSERT INTO appointment_slots (service_id, appointment_date, start_time, gender, capacity) VALUES (?, ?, ?, ?, ?)", (service_id, appointment_date, start_time, gender, capacity))

    def get_slot(self, service_id: int, appointment_date: str, start_time: str, gender: str) -> Optional[dict]:
        return self.fetch_one("SELECT * FROM appointment_slots WHERE service_id = ? AND appointment_date = ? AND start_time = ? AND gender = ?", (service_id, appointment_date, start_time, gender))

    def get_available_times(self, service_id: int, appointment_date: str, gender: str) -> list[dict]:
        return self.fetch_all(
            """SELECT s.*, sv.name AS service_name, 
               (SELECT COUNT(*) FROM appointments a WHERE a.service_id = s.service_id AND a.appointment_date = s.appointment_date AND a.start_time = s.start_time AND a.status = 'scheduled' AND (s.gender = 'all' OR a.gender = s.gender)) AS booked_count 
               FROM appointment_slots s INNER JOIN services sv ON sv.id = s.service_id 
               WHERE s.service_id = ? AND s.appointment_date = ? AND s.gender = ? ORDER BY s.start_time""",
            (service_id, appointment_date, gender)
        )

    def create_appointment_if_available(self, patient_id: int, service_id: int, appointment_date: str, start_time: str, end_time: str, gender: str, status: str = "scheduled", reason: Optional[str] = None, notes: Optional[str] = None, created_by: Optional[int] = None) -> Optional[int]:
        connection = get_connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            
            slot = connection.execute("SELECT id, capacity, gender FROM appointment_slots WHERE service_id = ? AND appointment_date = ? AND start_time = ? AND (gender = ? OR gender = 'all')", (service_id, appointment_date, start_time, gender)).fetchone()
            if slot is None:
                connection.rollback()
                return None

            if slot["gender"] == "all":
                booked = connection.execute("SELECT COUNT(*) AS count FROM appointments WHERE service_id = ? AND appointment_date = ? AND start_time = ? AND status = 'scheduled'", (service_id, appointment_date, start_time)).fetchone()["count"]
            else:
                booked = connection.execute("SELECT COUNT(*) AS count FROM appointments WHERE service_id = ? AND appointment_date = ? AND start_time = ? AND gender = ? AND status = 'scheduled'", (service_id, appointment_date, start_time, gender)).fetchone()["count"]
            
            if booked >= slot["capacity"]:
                connection.rollback()
                return None

            active_existing = connection.execute("SELECT id FROM appointments WHERE patient_id = ? AND service_id = ? AND status = 'scheduled'", (patient_id, service_id)).fetchone()
            if active_existing:
                connection.rollback()
                raise ValueError("active_appointment_exists")

            cursor = connection.execute("INSERT INTO appointments (patient_id, service_id, appointment_date, start_time, end_time, gender, status, reason, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (patient_id, service_id, appointment_date, start_time, end_time, gender, status, reason, notes, created_by))
            connection.commit()
            return cursor.lastrowid
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_appointment_by_id(self, appointment_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT a.*, s.name AS service_name, p.first_name AS patient_first_name, p.last_name AS patient_last_name, p.phone_number AS patient_phone, p.national_id AS patient_national_id FROM appointments a INNER JOIN services s ON s.id = a.service_id INNER JOIN patients p ON p.id = a.patient_id WHERE a.id = ?", (appointment_id,))

    def get_current_appointments_for_user(self, user_id: int) -> list[dict]:
        return self.fetch_all("SELECT a.*, s.name AS service_name, p.first_name AS patient_first_name, p.last_name AS patient_last_name, p.phone_number AS patient_phone, p.national_id AS patient_national_id FROM appointments a INNER JOIN services s ON s.id = a.service_id INNER JOIN patients p ON p.id = a.patient_id INNER JOIN user_patient_profiles upp ON upp.patient_id = p.id WHERE upp.user_id = ? AND a.status = 'scheduled' ORDER BY a.appointment_date, a.start_time", (user_id,))

    def get_appointment_history_for_user(self, user_id: int) -> list[dict]:
        return self.fetch_all("SELECT a.*, s.name AS service_name, p.first_name AS patient_first_name, p.last_name AS patient_last_name, p.phone_number AS patient_phone, p.national_id AS patient_national_id FROM appointments a INNER JOIN services s ON s.id = a.service_id INNER JOIN patients p ON p.id = a.patient_id INNER JOIN user_patient_profiles upp ON upp.patient_id = p.id WHERE upp.user_id = ? AND a.status != 'scheduled' ORDER BY a.appointment_date DESC, a.start_time DESC", (user_id,))

    def update_appointment_status(self, appointment_id: int, status: str) -> bool:
        with get_connection() as connection:
            cursor = connection.execute("UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, appointment_id))
            connection.commit()
            return cursor.rowcount > 0

    def cancel_appointment(self, appointment_id: int) -> bool:
        return self.update_appointment_status(appointment_id, "cancelled")

    def get_user_appointment(self, user_id: int, appointment_id: int) -> Optional[dict]:
        return self.fetch_one("SELECT a.*, s.name AS service_name, p.first_name AS patient_first_name, p.last_name AS patient_last_name, p.phone_number AS patient_phone, p.national_id AS patient_national_id FROM appointments a INNER JOIN services s ON s.id = a.service_id INNER JOIN patients p ON p.id = a.patient_id INNER JOIN user_patient_profiles upp ON upp.patient_id = p.id WHERE upp.user_id = ? AND a.id = ?", (user_id, appointment_id))

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        if row is None: return default
        return row["value"]

    def set_setting(self, key: str, value: str) -> None:
        self.execute("INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP", (key, value))

repository = Repository()