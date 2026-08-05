import sqlite3
import os
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "clinic_database.db")

def _apply_patches():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE appointments ADD COLUMN source VARCHAR(50) DEFAULT 'bot'")
        except sqlite3.OperationalError:
            pass
_apply_patches()

def get_dict_cursor(conn):
    conn.row_factory = sqlite3.Row
    return conn.cursor()

def get_dashboard_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        
        cursor.execute("SELECT COUNT(*) as total FROM patients")
        patients_count = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status IN ('scheduled', 'accepted')")
        active_appointments = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status = 'cancelled'")
        cancelled_appointments = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM services WHERE is_active = 1")
        active_services = cursor.fetchone()["total"]
        
        return {
            "total_patients": patients_count,
            "active_appointments": active_appointments,
            "cancelled_appointments": cancelled_appointments,
            "active_services": active_services
        }

def get_all_patients() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT * FROM patients ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_patient_by_national_id(national_id: str) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT * FROM patients WHERE national_id = ?", (national_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_patient_by_staff(first_name: str, last_name: str, national_id: str, phone_number: str, gender: str = "male", insurance: str = "none") -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO patients (first_name, last_name, national_id, phone_number, gender, insurance) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, national_id, phone_number, gender, insurance)
        )
        conn.commit()
        return cursor.lastrowid

def update_patient_info(patient_id: int, first_name: str, last_name: str, phone_number: str, gender: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE patients SET first_name = ?, last_name = ?, phone_number = ?, gender = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (first_name, last_name, phone_number, gender, patient_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_all_appointments() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        # در این کوئری، جنسیت بیمار (patient_gender) هم از دیتابیس خوانده می‌شود
        query = """
            SELECT a.*, p.first_name, p.last_name, p.national_id, p.phone_number, p.user_id, p.gender as patient_gender, s.name as base_service_name
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.id
            LEFT JOIN services s ON a.service_id = s.id
            ORDER BY a.appointment_date DESC, a.start_time ASC
        """
        cursor.execute(query)
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            base_name = d.get("base_service_name") or ""
            
            # اگر جنسیت نوبت all بود، جنسیت واقعی بیمار را جایگزین می‌کنیم
            target_gender = d.get("gender")
            if target_gender == "all" or not target_gender:
                target_gender = d.get("patient_gender")
            
            # الصاق خودکار کلمه آقایان و بانوان در بک‌اند
            gendered_services = ["بادکش", "حجامت عام", "زالودرمانی"]
            is_gendered = any(s in base_name for s in gendered_services)
            
            if is_gendered:
                if target_gender == "male":
                    d["service_name"] = f"{base_name} آقایان"
                elif target_gender == "female":
                    d["service_name"] = f"{base_name} بانوان"
                else:
                    d["service_name"] = base_name
            else:
                d["service_name"] = base_name
                
            results.append(d)
        return results

def update_appointment_status(appointment_id: int, status: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, appointment_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def create_appointment_by_staff(patient_id: int, service_id: int, appointment_date: str, start_time: str, gender: str = "all", source: str = "panel") -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (patient_id, service_id, appointment_date, start_time, end_time, gender, status, source) VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?)",
            (patient_id, service_id, appointment_date, start_time, "00:00", gender, source)
        )
        conn.commit()
        return cursor.lastrowid

def add_service(name: str, price: int = 0) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (name, price, is_active) VALUES (?, ?, 1)", (name, price))
        conn.commit()
        return cursor.lastrowid

def toggle_service_status(service_id: int, is_active: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE services SET is_active = ? WHERE id = ?", (is_active, service_id))
        conn.commit()
        return cursor.rowcount > 0