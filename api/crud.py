import sqlite3
import os
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "clinic_database.db")

def get_dict_cursor(conn):
    conn.row_factory = sqlite3.Row
    return conn.cursor()

def get_dashboard_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        
        cursor.execute("SELECT COUNT(*) as total FROM patients")
        patients_count = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status = 'scheduled'")
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

def get_all_appointments() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        query = """
            SELECT a.*, p.first_name, p.last_name, p.national_id, p.phone_number, s.name as service_name
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.id
            LEFT JOIN services s ON a.service_id = s.id
            ORDER BY a.appointment_date DESC, a.start_time ASC
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def update_appointment_status(appointment_id: int, status: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, appointment_id)
        )
        conn.commit()
        return cursor.rowcount > 0