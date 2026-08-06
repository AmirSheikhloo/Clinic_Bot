"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Download, UserPlus, X, CheckCircle, XCircle, Edit, Trash2, ChevronLeft, ChevronRight, AlertCircle } from "lucide-react";
import * as XLSX from "xlsx-js-style";

interface Patient { id: number; user_id?: number | null; first_name: string; last_name: string; national_id: string; phone_number: string; gender: string; insurance: string; created_at: string; }

const genderMap: Record<string, string> = { male: "آقا", female: "خانم", all: "عمومی" };

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

const toEnglishDigits = (str: string | null) => {
  if (!str) return "";
  const persianNumbers = [/۰/g, /۱/g, /۲/g, /۳/g, /۴/g, /۵/g, /۶/g, /۷/g, /۸/g, /۹/g];
  const arabicNumbers = [/٠/g, /١/g, /٢/g, /٣/g, /٤/g, /٥/g, /٦/g, /٧/g, /٨/g, /٩/g];
  let result = String(str);
  for (let i = 0; i < 10; i++) { result = result.replace(persianNumbers[i], String(i)).replace(arabicNumbers[i], String(i)); }
  return result;
};

const formatJalaliDateTime = (dbDateString: string) => {
  if (!dbDateString) return "";
  const safeDateString = dbDateString.includes("T") ? dbDateString : dbDateString.replace(" ", "T") + "Z";
  const date = new Date(safeDateString);
  return new Intl.DateTimeFormat("fa-IR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", numberingSystem: "latn" }).format(date);
};

const getPageNumbers = (current: number, total: number) => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (current <= 4) return [1, 2, 3, 4, 5, "...", total];
  if (current >= total - 3) return [1, "...", total - 4, total - 3, total - 2, total - 1, total];
  return [1, "...", current - 1, current, current + 1, "...", total];
};

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newNationalId, setNewNationalId] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newGender, setNewGender] = useState("male");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const [deletePatientData, setDeletePatientData] = useState<{id: number, name: string} | null>(null);

  const fetchPatientsData = useCallback(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/patients");
      const data: Patient[] = await res.json();
      const formattedData = data.sort((a, b) => b.id - a.id).map(p => ({
          ...p,
          national_id: toEnglishDigits(p.national_id),
          phone_number: toEnglishDigits(p.phone_number)
        }));
      setPatients(formattedData);
    } catch {
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { const init = async () => { await fetchPatientsData(); }; init(); }, [fetchPatientsData]);

  const openEditModal = (p: Patient) => {
    setEditMode(true); setEditId(p.id); setNewFirstName(p.first_name); setNewLastName(p.last_name); setNewNationalId(p.national_id || ""); setNewPhone(p.phone_number); setNewGender(p.gender || "male"); setIsModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletePatientData) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/patients/${deletePatientData.id}`, { method: "DELETE" });
      if (res.ok) { setDeletePatientData(null); fetchPatientsData(); }
    } catch {}
  };

  const handleCloseModal = () => { setIsModalOpen(false); setEditMode(false); setEditId(null); setNewFirstName(""); setNewLastName(""); setNewNationalId(""); setNewPhone(""); setNewGender("male"); setSubmitError(""); };

  const handleSubmitPatient = async (e: React.FormEvent) => {
    e.preventDefault(); setSubmitError("");
    if (!isValidIranianNationalId(newNationalId)) { setSubmitError("کد ملی وارد شده معتبر نیست."); return; }
    if (!/^09\d{9}$/.test(newPhone)) { setSubmitError("شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود."); return; }
    setSubmitLoading(true);
    const url = editMode ? `http://127.0.0.1:8000/api/patients/${editId}` : "http://127.0.0.1:8000/api/patients";
    const method = editMode ? "PUT" : "POST";
    try {
      const res = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify({ first_name: newFirstName, last_name: newLastName, national_id: newNationalId, phone_number: newPhone, gender: newGender, insurance: "none" }) });
      const data = await res.json();
      if (res.ok && data.success) { handleCloseModal(); fetchPatientsData(); } else { setSubmitError(data.detail || "خطا در عملیات."); }
    } catch { setSubmitError("خطا در ارتباط با سرور."); } finally { setSubmitLoading(false); }
  };

  const query = toEnglishDigits(searchQuery.trim());
  const filteredPatients = query ? patients.filter((p) => p.first_name.includes(query) || p.last_name.includes(query) || (p.national_id && p.national_id.includes(query)) || (p.phone_number && p.phone_number.includes(query))) : patients;
  const totalPages = Math.ceil(filteredPatients.length / rowsPerPage);
  const currentRows = filteredPatients.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

  const handleExportExcel = () => {
    const exportData = filteredPatients.map((p, index) => ({ "ردیف": index + 1, "نام و نام خانوادگی": `${p.first_name} ${p.last_name}`, "جنسیت": genderMap[p.gender] || p.gender || "نامشخص", "کد ملی": p.national_id || "ثبت نشده", "شماره تماس": p.phone_number, "منبع ثبت‌نام": p.user_id ? "ربات بله" : "پنل منشی", "شماره پرونده": p.id, "تاریخ و ساعت ثبت‌نام": formatJalaliDateTime(p.created_at) }));
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    worksheet['!cols'] = [ { wch: 8 }, { wch: 25 }, { wch: 10 }, { wch: 15 }, { wch: 15 }, { wch: 20 }, { wch: 15 }, { wch: 25 } ];
    for (const i in worksheet) { if (typeof worksheet[i] !== 'object') continue; worksheet[i].s = { alignment: { horizontal: "center", vertical: "center" } }; }
    const workbook = XLSX.utils.book_new(); workbook.Workbook = { Views: [{ RTL: true }] }; XLSX.utils.book_append_sheet(workbook, worksheet, "بیماران"); XLSX.writeFile(workbook, "Patients_List.xlsx");
  };

  if (loading) return <div className="flex h-screen items-center justify-center"><div className="text-xl font-bold text-blue-600">در حال بارگذاری لیست بیماران...</div></div>;

  return (
    <div className="min-h-screen px-8 w-full relative bg-gray-50">
      <header className="pt-12 pb-8 flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-2 border-b-transparent">
        <h1 className="text-3xl font-bold text-gray-800 leading-none">لیست بیماران</h1>
        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto items-center">
          <div className="relative w-full sm:w-80 h-11">
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none"><Search className="h-5 w-5 text-gray-400" /></div>
            <input type="text" className="block w-full h-full pr-10 pl-3 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 shadow-sm" placeholder="جستجو با نام، کد ملی یا شماره تماس..." value={searchQuery} onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }} />
          </div>
          <button onClick={() => { setEditMode(false); setIsModalOpen(true); }} className="flex h-11 items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 rounded-xl font-bold shadow-sm whitespace-nowrap cursor-pointer"><UserPlus className="w-5 h-5" /> ثبت بیمار جدید</button>
          <button onClick={handleExportExcel} className="flex h-11 items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-5 rounded-xl font-bold shadow-sm whitespace-nowrap cursor-pointer"><Download className="w-5 h-5" /> خروجی اکسل</button>
        </div>
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col mb-6">
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr><th className="p-4 text-gray-600 font-bold text-sm">ردیف</th><th className="p-4 text-gray-600 font-bold text-sm">نام و نام خانوادگی</th><th className="p-4 text-gray-600 font-bold text-sm">کد ملی</th><th className="p-4 text-gray-600 font-bold text-sm">شماره تماس</th><th className="p-4 text-gray-600 font-bold text-sm">جنسیت</th><th className="p-4 text-gray-600 font-bold text-sm">منبع ثبت‌نام</th><th className="p-4 text-gray-600 font-bold text-sm text-center">عملیات</th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {currentRows.map((patient, index) => (
                <tr key={patient.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-gray-800 font-bold">{(currentPage - 1) * rowsPerPage + index + 1}</td>
                  <td className="p-4 text-gray-800 font-bold">{patient.first_name} {patient.last_name}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm">{patient.national_id || "ثبت نشده"}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">{patient.phone_number}</td>
                  <td className="p-4 text-gray-600 text-sm font-medium">{genderMap[patient.gender] || "ثبت نشده"}</td>
                  <td className="p-4 text-sm font-medium"><span className={patient.user_id ? "text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg font-bold" : "text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg font-bold"}>{patient.user_id ? "ربات بله" : "پنل منشی"}</span></td>
                  <td className="p-4 flex justify-center gap-3">
                    <button onClick={() => openEditModal(patient)} className="flex items-center gap-1.5 px-4 py-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-xl text-xs font-bold transition-colors cursor-pointer"><Edit className="w-4 h-4" /> ویرایش</button>
                    <button onClick={() => setDeletePatientData({id: patient.id, name: `${patient.first_name} ${patient.last_name}`})} className="flex items-center gap-1.5 px-4 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-xl text-xs font-bold transition-colors cursor-pointer"><Trash2 className="w-4 h-4" /> حذف</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-center p-4 bg-white border border-gray-200 rounded-2xl shadow-sm gap-4 mb-8">
        <div className="flex items-center gap-2 text-sm font-bold text-gray-600">
          <span>نمایش</span>
          <select value={rowsPerPage} onChange={(e) => { setRowsPerPage(Number(e.target.value)); setCurrentPage(1); }} className="border border-gray-200 rounded-xl px-3 py-1.5 outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 cursor-pointer">
            {[5, 10, 25, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
          <span>ردیف</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1} className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-200 text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors cursor-pointer"><ChevronRight className="w-5 h-5" /></button>
          <div className="flex gap-1 flex-wrap justify-center px-2">
            {getPageNumbers(currentPage, totalPages).map((pageNum, idx) => (
              pageNum === "..." ? <span key={idx} className="w-10 h-10 flex items-center justify-center text-gray-400 font-bold">...</span> :
              <button key={idx} onClick={() => setCurrentPage(pageNum as number)} className={`w-10 h-10 flex items-center justify-center rounded-xl text-sm font-bold transition-all cursor-pointer ${currentPage === pageNum ? 'bg-blue-600 text-white shadow-md' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}`}>{pageNum}</button>
            ))}
          </div>
          <button onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages || totalPages === 0} className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-200 text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors cursor-pointer"><ChevronLeft className="w-5 h-5" /></button>
        </div>
      </div>

      {deletePatientData && (
        <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-gray-100">
            <div className="p-8">
              <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6"><AlertCircle className="w-10 h-10 text-red-500" /></div>
              <h3 className="text-2xl font-bold text-center text-gray-800 mb-3">حذف پرونده بیمار</h3>
              <p className="text-center text-gray-600 mb-8 leading-relaxed font-medium">آیا مطمئن هستید که می‌خواهید پرونده «<span className="font-bold text-gray-900">{deletePatientData.name}</span>» را حذف کنید؟</p>
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 mb-8">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-sm font-bold text-amber-800 leading-relaxed">نکته مهم: برای حفظ یکپارچگی سیستم، نوبت‌های قبلی این بیمار در جدول نوبت‌ها حفظ خواهند شد.</p>
                </div>
              </div>
              <div className="flex gap-4">
                <button onClick={() => setDeletePatientData(null)} className="flex-1 py-3.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-colors cursor-pointer">انصراف</button>
                <button onClick={confirmDelete} className="flex-1 py-3.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-bold transition-colors shadow-lg shadow-red-200 cursor-pointer">بله، حذف شود</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in p-4">
          <div className="bg-white w-full max-w-lg rounded-3xl shadow-xl overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-gray-50">
              <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">{editMode ? <Edit className="w-5 h-5 text-blue-600" /> : <UserPlus className="w-5 h-5 text-blue-600" />} {editMode ? "ویرایش اطلاعات بیمار" : "تشکیل پرونده بیمار جدید"}</h3>
              <button onClick={handleCloseModal} className="text-gray-400 hover:text-red-500 transition-colors cursor-pointer"><X className="w-6 h-6" /></button>
            </div>
            
            <form onSubmit={handleSubmitPatient} className="p-6 space-y-5">
              {submitError && <div className="p-3 bg-red-50 text-red-700 rounded-xl text-sm font-bold">{submitError}</div>}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">کد ملی:</label>
                <div className="relative">
                  <input type="text" placeholder="کد ملی ۱۰ رقمی..." className="w-full pl-12 pr-4 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-right font-mono tracking-widest placeholder:text-gray-400 placeholder:font-sans shadow-sm" dir="rtl" value={newNationalId} onChange={(e) => setNewNationalId(e.target.value.replace(/\D/g, '').slice(0, 10))} required />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center">
                    {newNationalId.length === 10 ? ( isValidIranianNationalId(newNationalId) ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" /> ) : ( <span className="flex items-center justify-center w-6 h-6 bg-gray-100 text-gray-500 text-xs font-bold rounded-md">{10 - newNationalId.length}</span> )}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-sm font-bold text-gray-700 mb-2">نام:</label><input type="text" value={newFirstName} onChange={e => setNewFirstName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" required /></div>
                <div><label className="block text-sm font-bold text-gray-700 mb-2">نام خانوادگی:</label><input type="text" value={newLastName} onChange={e => setNewLastName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" required /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">شماره تماس:</label>
                  <div className="relative">
                    <input type="text" value={newPhone} onChange={e => setNewPhone(e.target.value.replace(/\D/g, '').slice(0, 11))} placeholder="09123456789" dir="ltr" className="w-full pl-10 pr-3 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-center font-mono tracking-widest shadow-sm" required />
                    <div className="absolute left-2 top-1/2 -translate-y-1/2 flex items-center justify-center">
                      {newPhone.length === 11 ? ( newPhone.startsWith("09") ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" /> ) : ( <span className="flex items-center justify-center w-6 h-6 bg-blue-50 text-blue-600 text-xs font-bold rounded-md">{11 - newPhone.length}</span> )}
                    </div>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-2">جنسیت:</label>
                  <div className="flex bg-gray-100 p-1 rounded-xl border border-gray-200 h-12 items-center shadow-sm">
                    <button type="button" onClick={() => setNewGender('male')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all cursor-pointer ${newGender === 'male' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>آقا</button>
                    <button type="button" onClick={() => setNewGender('female')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all cursor-pointer ${newGender === 'female' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>خانم</button>
                  </div>
                </div>
              </div>
              <div className="pt-4 flex gap-3">
                <button type="button" onClick={handleCloseModal} className="flex-1 px-4 py-3.5 bg-gray-100 text-gray-700 rounded-xl font-bold hover:bg-gray-200 transition-colors cursor-pointer">انصراف</button>
                <button type="submit" disabled={submitLoading} className="flex-1 px-4 py-3.5 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-70 cursor-pointer">{submitLoading ? "در حال پردازش..." : (editMode ? "ذخیره تغییرات" : "ذخیره پرونده")}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}