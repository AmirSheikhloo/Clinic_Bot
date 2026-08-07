import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from datetime import date, timedelta, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "clinic_database.db")

def _apply_patches():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try: cursor.execute("CREATE TABLE IF NOT EXISTS settings (key VARCHAR PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE appointments ADD COLUMN source VARCHAR(50) DEFAULT 'bot'")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE patients ADD COLUMN is_active INTEGER DEFAULT 1")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE services ADD COLUMN has_gender INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE services ADD COLUMN is_deleted INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE services ADD COLUMN price INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass
        try: cursor.execute("CREATE TABLE IF NOT EXISTS overridden_dates (date VARCHAR, service_id INTEGER, PRIMARY KEY(date, service_id))")
        except sqlite3.OperationalError: pass
        try: cursor.execute("CREATE TABLE IF NOT EXISTS override_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, target_date VARCHAR, service_id INTEGER, service_name VARCHAR, details TEXT, status_msg VARCHAR, logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        except sqlite3.OperationalError: pass
        
        cursor.execute("UPDATE services SET has_gender = 1 WHERE name IN ('بادکش', 'حجامت عام', 'زالودرمانی') AND has_gender = 0")
        conn.commit()
    try:
        config = get_schedule_config()
        sync_future_slots(config)
    except Exception: pass

_apply_patches()

def get_dict_cursor(conn):
    conn.row_factory = sqlite3.Row
    return conn.cursor()

def get_general_settings() -> Dict[str, str]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings WHERE key IN ('clinic_name', 'clinic_phone', 'clinic_address', 'working_hours_text')")
        rows = cursor.fetchall()
        result = {"clinic_name": "", "clinic_phone": "", "clinic_address": "", "working_hours_text": ""}
        for r in rows:
            if r[1]: result[r[0]] = str(r[1])
        return result

def save_general_setting(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
        conn.commit()

def get_schedule_config() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'schedule_config'")
        row = cursor.fetchone()
        
        cursor.execute("SELECT id, name, has_gender FROM services WHERE is_deleted = 0")
        services = cursor.fetchall()
        
        config = None
        if row and row["value"]:
            try: config = json.loads(row["value"])
            except: pass
            
        if not config: config = {"working_days": [5,6,0,1,2,3], "booking_days_ahead": 7, "default_times": {}, "weekly_times": {}}
        if "default_times" not in config: config["default_times"] = {}
        if "weekly_times" not in config: config["weekly_times"] = {}
            
        changed = False
        for s in services:
            sid = str(s["id"])
            if sid not in config["default_times"]:
                config["default_times"][sid] = {}
                
            has_times = False
            for gender_key, times_list in config["default_times"][sid].items():
                if len(times_list) > 0:
                    has_times = True
                    break
                    
            if not has_times:
                if s["has_gender"] == 1:
                    config["default_times"][sid]["male"] = ["14:00", "15:00", "16:00", "17:00"]
                    config["default_times"][sid]["female"] = ["14:00", "15:00", "16:00", "17:00"]
                else:
                    config["default_times"][sid]["all"] = ["14:00", "15:00", "16:00", "17:00"]
                changed = True
                
        if changed:
            cursor.execute("INSERT INTO settings (key, value, updated_at) VALUES ('schedule_config', ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (json.dumps(config),))
            conn.commit()
            
        return config

def sync_future_slots(config: Dict[str, Any]):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        days_ahead = int(config.get("booking_days_ahead", 7))
        working_days = config.get("working_days", [])
        default_times = config.get("default_times", {})
        weekly_times = config.get("weekly_times", {})
        today = date.today()
        
        cursor.execute("SELECT date, service_id FROM overridden_dates")
        overridden = {(r[0], r[1]) for r in cursor.fetchall()}
        
        for offset in range(0, days_ahead + 1):
            curr_date = today + timedelta(days=offset)
            date_str = curr_date.isoformat()
            wd = str(curr_date.weekday())
            
            if int(wd) not in working_days: 
                cursor.execute("DELETE FROM appointment_slots WHERE appointment_date = ? AND service_id NOT IN (SELECT service_id FROM overridden_dates WHERE date = ?)", (date_str, date_str))
                continue
                
            all_services = set(list(default_times.keys()) + list(weekly_times.get(wd, {}).keys()))
            for s_id in all_services:
                if (date_str, int(s_id)) in overridden:
                    continue
                
                cursor.execute("DELETE FROM appointment_slots WHERE appointment_date = ? AND service_id = ?", (date_str, int(s_id)))
                
                s_times = weekly_times.get(wd, {}).get(s_id)
                if s_times is None or len(s_times) == 0:
                    s_times = default_times.get(s_id, {})
                    
                for gender, times in s_times.items():
                    for t in times:
                        cursor.execute("INSERT INTO appointment_slots (service_id, appointment_date, start_time, gender, capacity) VALUES (?, ?, ?, ?, 1)", (int(s_id), date_str, t, gender))
        
        cursor.execute("SELECT o.date, o.service_id, s.name FROM overridden_dates o JOIN services s ON o.service_id = s.id")
        active_overrides = cursor.fetchall()
        for ov in active_overrides:
            ov_date = datetime.strptime(ov[0], "%Y-%m-%d").date()
            if ov_date < today:
                cursor.execute("SELECT start_time, gender FROM appointment_slots WHERE appointment_date = ? AND service_id = ?", (ov[0], ov[1]))
                slots = cursor.fetchall()
                slots_data = [{"time": r[0], "gender": r[1]} for r in slots]
                status_msg = "به طور کامل تا پایان روز اعمال شد"
                cursor.execute("INSERT INTO override_logs (target_date, service_id, service_name, details, status_msg) VALUES (?, ?, ?, ?, ?)", (ov[0], ov[1], ov[2], json.dumps(slots_data), status_msg))
                cursor.execute("DELETE FROM overridden_dates WHERE date = ? AND service_id = ?", (ov[0], ov[1]))

        conn.commit()

def save_schedule_config(config: Dict[str, Any]):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO settings (key, value, updated_at) VALUES ('schedule_config', ?, CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (json.dumps(config),))
        conn.commit()
    sync_future_slots(config)

def get_date_slots(target_date: str, service_id: int) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT 1 FROM overridden_dates WHERE date = ? AND service_id = ?", (target_date, service_id))
        is_overridden = cursor.fetchone() is not None

        if is_overridden:
            cursor.execute("SELECT start_time as time, gender FROM appointment_slots WHERE appointment_date = ? AND service_id = ?", (target_date, service_id))
            return [dict(row) for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT value FROM settings WHERE key = 'schedule_config'")
            row = cursor.fetchone()
            if row and row["value"]:
                try:
                    config = json.loads(row["value"])
                    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
                    wd = str(target_dt.weekday())
                    if int(wd) not in config.get("working_days", []):
                        return []
                    weekly = config.get("weekly_times", {}).get(wd, {}).get(str(service_id))
                    if weekly is None or len(weekly) == 0:
                        weekly = config.get("default_times", {}).get(str(service_id), {})
                    computed_slots = []
                    for g, times in weekly.items():
                        for t in times:
                            computed_slots.append({"time": t, "gender": g})
                    return computed_slots
                except Exception: pass
            return []

def override_date_slots(target_date: str, service_id: int, new_slots: List[Dict[str, Any]]) -> List[int]:
    cancelled_bale_ids = []
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("INSERT OR IGNORE INTO overridden_dates (date, service_id) VALUES (?, ?)", (target_date, service_id))
        
        valid_times = [s["time"] for s in new_slots]
        if valid_times:
            placeholders = ",".join("?" for _ in valid_times)
            query_cancel = f"SELECT a.id, u.bale_user_id FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN users u ON p.user_id = u.id WHERE a.appointment_date = ? AND a.service_id = ? AND a.start_time NOT IN ({placeholders}) AND a.status = 'scheduled'"
            cursor.execute(query_cancel, [target_date, service_id] + valid_times)
        else:
            cursor.execute("SELECT a.id, u.bale_user_id FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN users u ON p.user_id = u.id WHERE a.appointment_date = ? AND a.service_id = ? AND a.status = 'scheduled'", (target_date, service_id))
            
        for row in cursor.fetchall():
            cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (row["id"],))
            if row["bale_user_id"]: cancelled_bale_ids.append(row["bale_user_id"])
            
        cursor.execute("DELETE FROM appointment_slots WHERE appointment_date = ? AND service_id = ?", (target_date, service_id))
        for slot in new_slots:
            cursor.execute("INSERT INTO appointment_slots (service_id, appointment_date, start_time, gender, capacity) VALUES (?, ?, ?, ?, 1)", (service_id, target_date, slot["time"], slot["gender"]))
        conn.commit()
    return cancelled_bale_ids

def get_overridden_dates() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("""
            SELECT o.date, o.service_id, s.name as service_name, s.has_gender
            FROM overridden_dates o
            JOIN services s ON o.service_id = s.id
            ORDER BY o.date DESC
        """)
        active_overrides = [dict(row) for row in cursor.fetchall()]
        for ov in active_overrides:
            cursor.execute("SELECT start_time as time, gender FROM appointment_slots WHERE appointment_date = ? AND service_id = ?", (ov["date"], ov["service_id"]))
            ov["slots"] = [dict(r) for r in cursor.fetchall()]
            
        cursor.execute("SELECT * FROM override_logs ORDER BY logged_at DESC LIMIT 100")
        history_logs = [dict(row) for row in cursor.fetchall()]
        for log in history_logs:
            try: log["slots"] = json.loads(log["details"])
            except: log["slots"] = []
            
        return {"active": active_overrides, "history": history_logs}

def reset_override(target_date: str, service_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now()
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        cursor.execute("SELECT name FROM services WHERE id = ?", (service_id,))
        s_row = cursor.fetchone()
        s_name = s_row[0] if s_row else "نامشخص"
        
        cursor.execute("SELECT start_time as time, gender FROM appointment_slots WHERE appointment_date = ? AND service_id = ?", (target_date, service_id))
        slots_data = [{"time": r[0], "gender": r[1]} for r in cursor.fetchall()]
        
        if now.date() < target_dt.date():
            status_msg = "بدون فعالیت (پیش از رسیدن به تاریخ مقرر) لغو شد"
        elif now.date() == target_dt.date():
            status_msg = f"از ساعت 00:00 تا {now.strftime('%H:%M')} فعال بود و سپس توسط مدیر لغو شد"
        else:
            status_msg = "به طور کامل تا پایان روز اعمال شد"
            
        cursor.execute("INSERT INTO override_logs (target_date, service_id, service_name, details, status_msg) VALUES (?, ?, ?, ?, ?)", (target_date, service_id, s_name, json.dumps(slots_data), status_msg))
        cursor.execute("DELETE FROM overridden_dates WHERE date = ? AND service_id = ?", (target_date, service_id))
        conn.commit()
        
    config = get_schedule_config()
    sync_future_slots(config)

def get_dashboard_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT COUNT(*) as total FROM patients WHERE is_active = 1")
        patients_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status IN ('scheduled', 'accepted')")
        active_appointments = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE status = 'cancelled'")
        cancelled_appointments = cursor.fetchone()["total"]
        today = date.today().isoformat()
        cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE appointment_date = ? AND status = 'scheduled'", (today,))
        today_appointments = cursor.fetchone()["total"]
        return {"total_patients": patients_count, "active_appointments": active_appointments, "cancelled_appointments": cancelled_appointments, "today_appointments": today_appointments}

def get_reports_stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status IN ('completed', 'accepted') THEN 1 ELSE 0 END) as success, SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as pending FROM appointments")
        row = cursor.fetchone()
        total_appts = row["total"] or 0
        success_appts = row["success"] or 0
        pending_appts = row["pending"] or 0
        success_rate = round((success_appts / total_appts) * 100) if total_appts > 0 else 0
        
        query_service = """
            SELECT s.name, COUNT(a.id) as total, 
            SUM(CASE WHEN a.status IN ('completed', 'accepted') THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN a.status = 'scheduled' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
            SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) as no_show
            FROM appointments a JOIN services s ON a.service_id = s.id
            GROUP BY s.id ORDER BY total DESC
        """
        cursor.execute(query_service)
        services_perf = [dict(r) for r in cursor.fetchall()]
        popular = services_perf[0]["name"] if services_perf else "---"
        return {"success_rate": success_rate, "popular_service": popular, "total_appointments": total_appts, "pending_appointments": pending_appts, "services_performance": services_perf}

def get_all_patients() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT * FROM patients WHERE is_active = 1 ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_patient_by_national_id(national_id: str) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT * FROM patients WHERE national_id = ? AND is_active = 1", (national_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_patient_by_staff(first_name: str, last_name: str, national_id: str, phone_number: str, gender: str = "male", insurance: str = "none") -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_active FROM patients WHERE national_id = ?", (national_id,))
        row = cursor.fetchone()
        if row:
            if row[1] == 0:
                cursor.execute("UPDATE patients SET first_name = ?, last_name = ?, phone_number = ?, gender = ?, insurance = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (first_name, last_name, phone_number, gender, insurance, row[0]))
                conn.commit()
                return row[0]
            else: raise sqlite3.IntegrityError("UNIQUE constraint failed")
        cursor.execute("INSERT INTO patients (first_name, last_name, national_id, phone_number, gender, insurance, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)", (first_name, last_name, national_id, phone_number, gender, insurance))
        conn.commit()
        return cursor.lastrowid

def update_patient_info(patient_id: int, first_name: str, last_name: str, phone_number: str, gender: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE patients SET first_name = ?, last_name = ?, phone_number = ?, gender = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (first_name, last_name, phone_number, gender, patient_id))
        conn.commit()
        return cursor.rowcount > 0

def soft_delete_patient(patient_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE patients SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (patient_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_all_appointments() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        query = "SELECT a.*, p.first_name, p.last_name, p.national_id, p.phone_number, p.user_id, p.gender as patient_gender, s.name as base_service_name FROM appointments a LEFT JOIN patients p ON a.patient_id = p.id LEFT JOIN services s ON a.service_id = s.id ORDER BY a.appointment_date DESC, a.start_time ASC"
        cursor.execute(query)
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            base_name = d.get("base_service_name") or ""
            target_gender = d.get("gender")
            if target_gender == "all" or not target_gender: target_gender = d.get("patient_gender")
            if any(s in base_name for s in ["بادکش", "حجامت عام", "زالودرمانی"]):
                if target_gender == "male": d["service_name"] = f"{base_name} آقایان"
                elif target_gender == "female": d["service_name"] = f"{base_name} بانوان"
                else: d["service_name"] = base_name
            else: d["service_name"] = base_name
            results.append(d)
        return results

def get_todays_appointments() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        today = date.today().isoformat()
        query = "SELECT a.*, p.first_name, p.last_name, p.national_id, p.phone_number, p.gender as patient_gender, s.name as base_service_name FROM appointments a LEFT JOIN patients p ON a.patient_id = p.id LEFT JOIN services s ON a.service_id = s.id WHERE a.appointment_date = ? ORDER BY a.start_time ASC"
        cursor.execute(query, (today,))
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            base_name = d.get("base_service_name") or ""
            target_gender = d.get("gender")
            if target_gender == "all" or not target_gender: target_gender = d.get("patient_gender")
            if any(s in base_name for s in ["بادکش", "حجامت عام", "زالودرمانی"]):
                if target_gender == "male": d["service_name"] = f"{base_name} آقایان"
                elif target_gender == "female": d["service_name"] = f"{base_name} بانوان"
                else: d["service_name"] = base_name
            else: d["service_name"] = base_name
            results.append(d)
        return results

def get_appointment_with_user_info(appointment_id: int) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        query = "SELECT a.*, p.first_name, p.last_name, s.name as service_name, u.bale_user_id FROM appointments a LEFT JOIN patients p ON a.patient_id = p.id LEFT JOIN users u ON p.user_id = u.id LEFT JOIN services s ON a.service_id = s.id WHERE a.id = ?"
        cursor.execute(query, (appointment_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_appointment_status(appointment_id: int, status: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, appointment_id))
        conn.commit()
        return cursor.rowcount > 0

def create_appointment_by_staff(patient_id: int, service_id: int, appointment_date: str, start_time: str, gender: str = "all", source: str = "panel") -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO appointments (patient_id, service_id, appointment_date, start_time, end_time, gender, status, source) VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?)", (patient_id, service_id, appointment_date, start_time, "00:00", gender, source))
        conn.commit()
        return cursor.lastrowid

def get_all_services_admin() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = get_dict_cursor(conn)
        cursor.execute("SELECT * FROM services WHERE is_deleted = 0 ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def add_service(name: str, price: int = 0, has_gender: int = 0) -> int:
    _apply_patches()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM services WHERE name = ? AND is_deleted = 0", (name,))
        if cursor.fetchone(): raise ValueError("DuplicateService")
        cursor.execute("INSERT INTO services (name, price, has_gender, is_active, is_deleted) VALUES (?, ?, ?, 1, 0)", (name, price, has_gender))
        conn.commit()
        return cursor.lastrowid

def toggle_service_status(service_id: int, is_active: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE services SET is_active = ? WHERE id = ?", (is_active, service_id))
        conn.commit()
        return cursor.rowcount > 0

def update_service_info(service_id: int, name: str, price: int, has_gender: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM services WHERE name = ? AND id != ? AND is_deleted = 0", (name, service_id))
        if cursor.fetchone(): raise ValueError("DuplicateService")
        cursor.execute("UPDATE services SET name = ?, price = ?, has_gender = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (name, price, has_gender, service_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_service(service_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE services SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (service_id,))
        conn.commit()
        return cursor.rowcount > 0