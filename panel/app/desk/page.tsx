"use client";

import { useState, useEffect, useRef } from "react";
import { Search, UserPlus, CalendarPlus, CheckCircle, Save, X, Trash2, XCircle, Edit, ChevronLeft } from "lucide-react";
import DatePicker, { DateObject } from "react-multi-date-picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import gregorian from "react-date-object/calendars/gregorian";
import gregorian_en from "react-date-object/locales/gregorian_en";

const custom_fa = { ...persian_fa, digits: ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] };
const genderMap: Record<string, string> = { male: "آقا", female: "خانم" };

interface Patient { id?: number; first_name: string; last_name: string; national_id: string; phone_number: string; gender?: string; }
interface Service { id: number; name: string; }

const isValidIranianNationalId = (input: string) => {
  if (!/^\d{10}$/.test(input)) return false;
  const isAllSame = /^(.)\1{9}$/.test(input);
  if (isAllSame) return false;
  const check = parseInt(input[9]);
  let sum = 0;
  for (let i = 0; i < 9; ++i) { sum += parseInt(input[i]) * (10 - i); }
  const mod = sum % 11;
  return (mod < 2 && check === mod) || (mod >= 2 && check === 11 - mod);
};

const getServiceDisplayName = (serviceName: string, gender?: string) => {
  if (!serviceName) return "";
  let display = serviceName;
  if (["بادکش", "حجامت عام", "زالودرمانی", "ماساژ"].some(s => display.includes(s))) {
    if (gender === "male") display += " آقایان"; else if (gender === "female") display += " بانوان";
  }
  return display;
};

const getCurrentTime = () => new DateObject({ calendar: persian, locale: custom_fa }).format("HH:mm");

const CustomSelect = ({ value, options, onChange, placeholder = "انتخاب کنید...", disabled = false, grid = false }: { value: string, options: {value: string, label: string}[], onChange: (val: string) => void, placeholder?: string, disabled?: boolean, grid?: boolean }) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selectedOption = options.find(o => o.value === value);

  return (
    <div className="relative w-full" ref={ref}>
      <div onClick={() => !disabled && setIsOpen(!isOpen)} 
           className={`w-full px-4 h-12 border rounded-xl flex items-center justify-between shadow-sm transition-all ${disabled ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed' : 'bg-white border-gray-200 cursor-pointer hover:border-blue-400 focus:ring-2 focus:ring-blue-500'}`}>
        <span className={`font-bold text-sm truncate ${selectedOption ? 'text-gray-700' : 'text-gray-400'}`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronLeft className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? '-rotate-90' : ''}`} />
      </div>
      {isOpen && !disabled && (
        <div className="absolute z-50 mt-2 w-full min-w-max bg-white border border-gray-100 rounded-xl shadow-xl overflow-hidden p-2 right-0 origin-top animate-fade-in">
          <div className={`max-h-64 overflow-y-auto ${grid && options.length > 5 ? 'grid grid-cols-1 sm:grid-cols-2 gap-1' : 'flex flex-col gap-1'}`}>
            {options.map((opt) => (
              <div key={opt.value} onClick={() => { onChange(opt.value); setIsOpen(false); }}
                   className={`px-3 py-2.5 rounded-lg font-bold text-sm cursor-pointer transition-colors flex items-center gap-2 ${value === opt.value ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'}`}>
                {value === opt.value ? <CheckCircle className="w-4 h-4 text-blue-600 shrink-0"/> : <div className="w-4 h-4 shrink-0"/>}
                <span className="truncate">{opt.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const TimeInput = ({ value, onChange }: { value: string, onChange: (val: string) => void }) => {
  const [h, m] = (value || "00:00").split(":");
  const minuteRef = useRef<HTMLInputElement>(null);
  const handleHourChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, '');
    if (!val) { onChange(`:${m}`); return; }
    if (val.length > 2) val = val.slice(-2);
    if (val === "24") val = "00"; else if (parseInt(val) > 23) val = val.slice(-1);
    if (val.length === 1 && parseInt(val) >= 3) val = '0' + val;
    onChange(`${val}:${m}`);
    if (val.length === 2) minuteRef.current?.focus();
  };
  const handleMinuteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, '');
    if (!val) { onChange(`${h}:`); return; }
    if (val.length > 2) val = val.slice(-2);
    if (parseInt(val) > 59) val = val.slice(-1);
    if (val.length === 1 && parseInt(val) >= 6) val = '0' + val;
    onChange(`${h}:${val}`);
  };
  const handleHourBlur = (e: React.FocusEvent<HTMLInputElement>) => { const val = e.target.value.replace(/\D/g, ''); if (val.length === 1) onChange(`0${val}:${m}`); if (!val) onChange(`00:${m}`); };
  const handleMinuteBlur = (e: React.FocusEvent<HTMLInputElement>) => { const val = e.target.value.replace(/\D/g, ''); if (val.length === 1) onChange(`${h}:0${val}`); if (!val) onChange(`${h}:00`); };
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, type: 'h' | 'm') => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (type === 'h') { const newH = (parseInt(h || '0') + 1) % 24; onChange(`${String(newH).padStart(2, '0')}:${m}`); }
      else { const newM = (parseInt(m || '0') + 1) % 60; onChange(`${h}:${String(newM).padStart(2, '0')}`); }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (type === 'h') { const newH = (parseInt(h || '0') - 1 + 24) % 24; onChange(`${String(newH).padStart(2, '0')}:${m}`); }
      else { const newM = (parseInt(m || '0') - 1 + 60) % 60; onChange(`${h}:${String(newM).padStart(2, '0')}`); }
    }
  };
  return (
    <div className="flex items-center justify-center w-full px-4 h-12 border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 bg-white transition-all shadow-sm cursor-text" dir="ltr">
      <input type="tel" inputMode="numeric" value={h} onChange={handleHourChange} onBlur={handleHourBlur} onFocus={e => e.target.select()} onKeyDown={e => handleKeyDown(e, 'h')} className="w-10 text-center font-mono text-lg outline-none bg-transparent placeholder-gray-300 text-gray-800 font-bold" placeholder="00" />
      <span className="font-extrabold text-gray-400 mx-1 pb-1">:</span>
      <input ref={minuteRef} type="tel" inputMode="numeric" value={m} onChange={handleMinuteChange} onBlur={handleMinuteBlur} onFocus={e => e.target.select()} onKeyDown={e => handleKeyDown(e, 'm')} className="w-10 text-center font-mono text-lg outline-none bg-transparent placeholder-gray-300 text-gray-800 font-bold" placeholder="00" />
    </div>
  );
};

export default function FastDeskPage() {
  const [nationalId, setNationalId] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [newPatientMode, setNewPatientMode] = useState(false);
  const [services, setServices] = useState<Service[]>([]);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [patientGender, setPatientGender] = useState("male");

  const [serviceId, setServiceId] = useState("");
  const [dateObj, setDateObj] = useState<DateObject>(new DateObject({ calendar: persian, locale: custom_fa }));
  const [time, setTime] = useState(getCurrentTime());

  const [isEditing, setIsEditing] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  
  const [isRestored, setIsRestored] = useState(false);

  useEffect(() => {
    const loadState = async () => {
      const saved = localStorage.getItem("deskState");
      if (saved) {
        try {
          const state = JSON.parse(saved);
          setNationalId(state.nationalId || ""); setFirstName(state.firstName || ""); setLastName(state.lastName || ""); setPhone(state.phone || ""); setPatientGender(state.patientGender || "male"); setServiceId(state.serviceId || ""); setTime(state.time || getCurrentTime()); setPatient(state.patient || null); setNewPatientMode(state.newPatientMode || false);
        } catch {}
      }
      setIsRestored(true);
    };
    loadState();
    fetch("http://127.0.0.1:8000/api/services").then(res => res.json()).then(data => setServices(data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (isRestored) {
      localStorage.setItem("deskState", JSON.stringify({ nationalId, firstName, lastName, phone, patientGender, serviceId, time, patient, newPatientMode }));
    }
  }, [nationalId, firstName, lastName, phone, patientGender, serviceId, time, patient, newPatientMode, isRestored]);

  const clearDesk = () => {
    localStorage.removeItem("deskState"); setNationalId(""); setFirstName(""); setLastName(""); setPhone(""); setPatientGender("male"); setServiceId(""); setDateObj(new DateObject({ calendar: persian, locale: custom_fa })); setTime(getCurrentTime()); setPatient(null); setNewPatientMode(false); setIsEditing(false); setErrorMsg(""); setSuccessMsg("");
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValidIranianNationalId(nationalId)) { setErrorMsg("کد ملی وارد شده معتبر نیست (فرمت الگوریتم اشتباه است)."); return; }
    setSearchLoading(true); setPatient(null); setNewPatientMode(false); setSuccessMsg(""); setErrorMsg(""); setIsEditing(false);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/patients/search/${nationalId}`);
      if (res.ok) setPatient(await res.json()); else setNewPatientMode(true);
    } catch { setNewPatientMode(true); } finally { setSearchLoading(false); }
  };

  const handleEditPatient = async () => {
    if (!patient?.id) return;
    if (!/^09\d{9}$/.test(phone)) { setErrorMsg("شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود."); return; }
    setEditLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/patients/${patient.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ first_name: firstName, last_name: lastName, phone_number: phone, gender: patientGender }) });
      if (res.ok) {
        setPatient({ ...patient, first_name: firstName, last_name: lastName, phone_number: phone, gender: patientGender });
        setIsEditing(false); setSuccessMsg("اطلاعات بیمار با موفقیت ویرایش شد."); setTimeout(() => setSuccessMsg(""), 3000);
      } else { setErrorMsg((await res.json()).detail || "خطا در ویرایش اطلاعات."); }
    } catch { setErrorMsg("خطا در ارتباط با سرور."); } finally { setEditLoading(false); }
  };

  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setErrorMsg(""); setSuccessMsg("");
    if (!isValidIranianNationalId(nationalId)) { setErrorMsg("کد ملی وارد شده معتبر نیست."); return; }
    if (newPatientMode && !/^09\d{9}$/.test(phone)) { setErrorMsg("شماره موبایل باید ۱۱ رقم باشد و حتماً با 09 شروع شود."); return; }
    if (!dateObj || !time || !serviceId || time.includes(":_") || time.includes("_")) { setErrorMsg("لطفاً خدمت، تاریخ و ساعت را کامل و صحیح انتخاب کنید."); return; }
    const currentGender = patient ? patient.gender : patientGender;
    const gregorianDate = new DateObject(dateObj).convert(gregorian, gregorian_en).format("YYYY-MM-DD");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/desk/book", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ national_id: nationalId, first_name: newPatientMode ? firstName : undefined, last_name: newPatientMode ? lastName : undefined, phone_number: newPatientMode ? phone : undefined, patient_gender: newPatientMode ? patientGender : undefined, service_id: parseInt(serviceId), appointment_date: gregorianDate, start_time: time, gender: currentGender || "all" }) });
      const data = await res.json();
      if (res.ok && data.success) {
        setSuccessMsg(`نوبت با موفقیت ثبت شد. کد پیگیری: CF-${String(data.appointment_id).padStart(6, '0')}`);
        setServiceId(""); setDateObj(new DateObject({ calendar: persian, locale: custom_fa })); setTime(getCurrentTime()); setPatient(null); setNewPatientMode(false); setNationalId(""); setFirstName(""); setLastName(""); setPhone(""); setPatientGender("male");
      } else { setErrorMsg(data.detail || "خطا در ثبت نوبت."); }
    } catch { setErrorMsg("خطا در ارتباط با سرور."); }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLFormElement>) => { if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'BUTTON') e.preventDefault(); };
  
  const currentActiveGender = patient ? patient.gender : patientGender;
  const serviceOptions = services.map(s => ({
    value: s.id.toString(),
    label: getServiceDisplayName(s.name, currentActiveGender)
  }));

  return (
    <div className="min-h-screen px-8 w-full relative bg-gray-50">
      <header className="pt-12 pb-8 flex items-center justify-between mb-2 border-b-transparent">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 leading-none">میز کار سریع منشی</h1>
        </div>
        {(patient || newPatientMode || nationalId) && (
          <button onClick={clearDesk} className="flex items-center justify-center gap-2.5 bg-red-50 hover:bg-red-100 text-red-600 px-6 h-12 rounded-xl text-sm font-bold transition-all shadow-sm border border-red-100 cursor-pointer">
            <Trash2 className="w-5 h-5" /> انصراف و پاک کردن میز
          </button>
        )}
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2"><Search className="w-5 h-5 text-blue-600" /> استعلام و جستجوی بیمار</h2>
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="relative flex-1">
              <input type="text" placeholder="کد ملی ۱۰ رقمی را وارد کنید..." className="w-full pl-12 pr-4 h-12 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-right font-mono tracking-widest placeholder:text-gray-400 placeholder:font-sans shadow-sm" dir="rtl" value={nationalId} onChange={(e) => setNationalId(e.target.value.replace(/\D/g, '').slice(0, 10))} required />
              <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center">
                {nationalId.length === 10 ? ( isValidIranianNationalId(nationalId) ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" /> ) : ( <span className="flex items-center justify-center w-6 h-6 bg-gray-100 text-gray-500 text-xs font-bold rounded-md">{10 - nationalId.length}</span> )}
              </div>
            </div>
            <button type="submit" disabled={searchLoading} className="bg-blue-600 hover:bg-blue-700 text-white px-6 h-12 rounded-xl font-bold transition-colors whitespace-nowrap cursor-pointer shadow-sm">{searchLoading ? "..." : "بررسی کد"}</button>
          </form>

          {newPatientMode && (
            <div className="mt-8 p-6 bg-blue-50 border border-blue-100 rounded-xl animate-fade-in shadow-sm">
              <h3 className="text-lg font-bold text-blue-800 mb-4 flex items-center gap-2"><UserPlus className="w-5 h-5" /> بیمار جدید (اطلاعات را تکمیل کنید)</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-bold text-blue-900 mb-2">نام:</label><input type="text" value={firstName} onChange={e => setFirstName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-12 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" required /></div>
                  <div><label className="block text-sm font-bold text-blue-900 mb-2">نام خانوادگی:</label><input type="text" value={lastName} onChange={e => setLastName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-12 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" required /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">شماره تماس:</label>
                    <div className="relative">
                      <input type="text" value={phone} onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))} placeholder="09123456789" dir="ltr" className="w-full pl-10 pr-3 h-12 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-center font-mono tracking-widest shadow-sm" required />
                      <div className="absolute left-2 top-1/2 -translate-y-1/2 flex items-center justify-center">
                        {phone.length === 11 ? ( phone.startsWith("09") ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" /> ) : ( <span className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-xs font-bold rounded-md">{11 - phone.length}</span> )}
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">جنسیت:</label>
                    <div className="flex bg-blue-100/50 p-1 rounded-xl border border-blue-200/50 h-12 items-center shadow-sm">
                      <button type="button" onClick={() => setPatientGender('male')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all cursor-pointer ${patientGender === 'male' ? 'bg-white text-blue-600 shadow-sm' : 'text-blue-500 hover:text-blue-700'}`}>آقا</button>
                      <button type="button" onClick={() => setPatientGender('female')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all cursor-pointer ${patientGender === 'female' ? 'bg-white text-blue-600 shadow-sm' : 'text-blue-500 hover:text-blue-700'}`}>خانم</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {patient && !isEditing && (
            <div className="mt-8 p-6 bg-emerald-50 border border-emerald-100 rounded-xl relative animate-fade-in shadow-sm">
              <button onClick={() => { setFirstName(patient.first_name); setLastName(patient.last_name); setPhone(patient.phone_number); setPatientGender(patient.gender || "male"); setIsEditing(true); }} className="absolute top-4 left-4 flex items-center gap-1.5 text-sm bg-white border border-emerald-200 text-emerald-700 px-4 py-2 rounded-lg hover:bg-emerald-100 transition-colors shadow-sm font-bold cursor-pointer"><Edit className="w-4 h-4" /> ویرایش</button>
              <h3 className="text-lg font-bold text-emerald-800 mb-4 flex items-center gap-2"><CheckCircle className="w-5 h-5" /> پرونده بیمار یافت شد</h3>
              <div className="grid grid-cols-2 gap-y-4 gap-x-2 text-sm text-emerald-900 mt-6">
                <p><span className="font-bold">نام:</span> {patient.first_name} {patient.last_name}</p>
                <p><span className="font-bold">شماره پرونده:</span> #{patient.id}</p>
                <p><span className="font-bold">کد ملی:</span> <span dir="ltr" className="font-mono">{patient.national_id}</span></p>
                <p><span className="font-bold">شماره تماس:</span> <span dir="ltr" className="font-mono">{patient.phone_number}</span></p>
                <p><span className="font-bold">جنسیت:</span> {patient.gender ? genderMap[patient.gender] || patient.gender : "ثبت نشده"}</p>
              </div>
            </div>
          )}

          {patient && isEditing && (
            <div className="mt-8 p-6 bg-blue-50 border border-blue-100 rounded-xl animate-fade-in shadow-sm">
              <h3 className="text-lg font-bold text-blue-800 mb-4 flex items-center gap-2"><Edit className="w-5 h-5" /> تصحیح اطلاعات بیمار</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-bold text-blue-900 mb-2">نام:</label><input type="text" value={firstName} onChange={e => setFirstName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-12 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" /></div>
                  <div><label className="block text-sm font-bold text-blue-900 mb-2">نام خانوادگی:</label><input type="text" value={lastName} onChange={e => setLastName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-12 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" /></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">شماره تماس جدید:</label>
                    <div className="relative">
                      <input type="text" value={phone} onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))} dir="ltr" className="w-full pl-10 pr-3 h-12 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-center font-mono tracking-widest shadow-sm" />
                      <div className="absolute left-2 top-1/2 -translate-y-1/2 flex items-center justify-center">
                        {phone.length === 11 ? ( phone.startsWith("09") ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" /> ) : ( <span className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-xs font-bold rounded-md">{11 - phone.length}</span> )}
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-blue-900 mb-2">جنسیت:</label>
                    <div className="flex bg-gray-100 p-1 rounded-xl border border-gray-200 h-12 items-center shadow-sm">
                      <button type="button" onClick={() => setPatientGender('male')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all cursor-pointer ${patientGender === 'male' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>آقا</button>
                      <button type="button" onClick={() => setPatientGender('female')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all cursor-pointer ${patientGender === 'female' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>خانم</button>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <button onClick={() => setIsEditing(false)} className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 font-bold px-6 py-3.5 rounded-xl flex items-center justify-center gap-2 shadow-sm cursor-pointer"><X className="w-5 h-5" /> انصراف</button>
                  <button onClick={handleEditPatient} disabled={editLoading} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 rounded-xl flex items-center justify-center gap-2 shadow-sm cursor-pointer disabled:opacity-70"><Save className="w-5 h-5" /> {editLoading ? "در حال پردازش..." : "ذخیره تغییرات"}</button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className={`p-6 rounded-2xl shadow-sm border border-gray-100 transition-all ${(patient || newPatientMode) ? 'bg-white opacity-100' : 'bg-gray-100 opacity-50 pointer-events-none'}`}>
          <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2"><CalendarPlus className="w-5 h-5 text-blue-600" /> ثبت نوبت</h2>
          {successMsg && <div className="mb-6 p-4 bg-green-50 text-green-700 border border-green-100 rounded-xl text-center font-bold shadow-sm">{successMsg}</div>}
          {errorMsg && <div className="mb-6 p-4 bg-red-50 text-red-700 border border-red-100 rounded-xl text-center font-bold shadow-sm">{errorMsg}</div>}
          <form onSubmit={handleFinalSubmit} onKeyDown={handleKeyDown} className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">انتخاب خدمت:</label>
              <CustomSelect 
                value={serviceId} 
                onChange={setServiceId} 
                options={serviceOptions} 
                placeholder="یک خدمت را انتخاب کنید..." 
                grid={true}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col relative">
                <label className="block text-sm font-bold text-gray-700 mb-2">انتخاب تاریخ:</label>
                <DatePicker calendar={persian} locale={custom_fa} value={dateObj} onChange={(dateObject: DateObject | null) => { if (dateObject) setDateObj(dateObject); }} containerClassName="w-full" inputClass="w-full px-4 h-12 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-center font-mono font-bold text-lg cursor-pointer shadow-sm" editable={false} />
              </div>
              <div className="flex flex-col relative">
                <label className="block text-sm font-bold text-gray-700 mb-2">انتخاب ساعت:</label>
                <TimeInput value={time} onChange={setTime} />
              </div>
            </div>
            <button type="submit" disabled={!(patient || newPatientMode) || isEditing} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-14 rounded-xl transition-colors mt-6 shadow-md disabled:opacity-70 cursor-pointer text-lg">
              ثبت نهایی (بیمار و نوبت)
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}