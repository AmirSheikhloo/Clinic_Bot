"use client";

import { useState, useEffect } from "react";
import { Search, Download, UserPlus, X, CheckCircle, XCircle } from "lucide-react";
import * as XLSX from "xlsx-js-style";

interface Patient {
  id: number;
  user_id?: number | null;
  first_name: string;
  last_name: string;
  national_id: string;
  phone_number: string;
  gender: string;
  insurance: string;
  created_at: string;
}

const genderMap: Record<string, string> = {
  male: "آقا",
  female: "خانم",
  all: "عمومی"
};

const isValidIranianNationalId = (input: string) => {
  if (!/^\d{10}$/.test(input)) return false;
  const isAllSame = /^(.)\1{9}$/.test(input);
  if (isAllSame) return false;

  const check = parseInt(input[9]);
  let sum = 0;
  for (let i = 0; i < 9; ++i) {
    sum += parseInt(input[i]) * (10 - i);
  }
  const mod = sum % 11;
  return (mod < 2 && check === mod) || (mod >= 2 && check === 11 - mod);
};

const toEnglishDigits = (str: string | null) => {
  if (!str) return "";
  const persianNumbers = [/۰/g, /۱/g, /۲/g, /۳/g, /۴/g, /۵/g, /۶/g, /۷/g, /۸/g, /۹/g];
  const arabicNumbers = [/٠/g, /١/g, /٢/g, /٣/g, /٤/g, /٥/g, /٦/g, /٧/g, /٨/g, /٩/g];
  let result = String(str);
  for (let i = 0; i < 10; i++) {
    result = result.replace(persianNumbers[i], String(i)).replace(arabicNumbers[i], String(i));
  }
  return result;
};

const formatJalaliDateTime = (dbDateString: string) => {
  if (!dbDateString) return "";
  const safeDateString = dbDateString.includes("T") ? dbDateString : dbDateString.replace(" ", "T") + "Z";
  const date = new Date(safeDateString);
  return new Intl.DateTimeFormat("fa-IR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    numberingSystem: "latn",
  }).format(date);
};

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newFirstName, setNewFirstName] = useState("");
  const [newLastName, setNewLastName] = useState("");
  const [newNationalId, setNewNationalId] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newGender, setNewGender] = useState("male");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const fetchPatientsData = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/patients");
      const data: Patient[] = await res.json();
      
      const formattedData = data
        .sort((a, b) => b.id - a.id)
        .map(p => ({
          ...p,
          national_id: toEnglishDigits(p.national_id),
          phone_number: toEnglishDigits(p.phone_number)
        }));
        
      setPatients(formattedData);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // راهکار قطعی برای رفع ارور react-hooks/set-state-in-effect
    const initFetch = async () => {
      await fetchPatientsData();
    };
    initFetch();
  }, []);

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setNewFirstName("");
    setNewLastName("");
    setNewNationalId("");
    setNewPhone("");
    setNewGender("male");
    setSubmitError("");
  };

  const handleCreatePatient = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError("");

    if (!isValidIranianNationalId(newNationalId)) {
      setSubmitError("کد ملی وارد شده معتبر نیست.");
      return;
    }
    if (!/^09\d{9}$/.test(newPhone)) {
      setSubmitError("شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.");
      return;
    }

    setSubmitLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/patients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: newFirstName,
          last_name: newLastName,
          national_id: newNationalId,
          phone_number: newPhone,
          gender: newGender,
          insurance: "none"
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        handleCloseModal();
        fetchPatientsData();
      } else {
        setSubmitError(data.detail || "خطا در ثبت بیمار.");
      }
    } catch {
      setSubmitError("خطا در ارتباط با سرور.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const query = toEnglishDigits(searchQuery.trim());
  const filteredPatients = query
    ? patients.filter(
        (p) =>
          p.first_name.includes(query) ||
          p.last_name.includes(query) ||
          (p.national_id && p.national_id.includes(query)) ||
          (p.phone_number && p.phone_number.includes(query))
      )
    : patients;

  const handleExportExcel = () => {
    const exportData = filteredPatients.map((p, index) => ({
      "ردیف": index + 1,
      "نام و نام خانوادگی": `${p.first_name} ${p.last_name}`,
      "جنسیت": genderMap[p.gender] || p.gender || "نامشخص",
      "کد ملی": p.national_id || "ثبت نشده",
      "شماره تماس": p.phone_number,
      "منبع ثبت‌نام": p.user_id ? "ربات بله / تلگرام" : "پنل مدیریت (توسط منشی)",
      "شماره پرونده": p.id,
      "تاریخ و ساعت ثبت‌نام": formatJalaliDateTime(p.created_at)
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    worksheet['!cols'] = [ { wch: 8 }, { wch: 25 }, { wch: 10 }, { wch: 15 }, { wch: 15 }, { wch: 25 }, { wch: 15 }, { wch: 25 } ];
    for (const i in worksheet) {
      if (typeof worksheet[i] !== 'object') continue;
      worksheet[i].s = { alignment: { horizontal: "center", vertical: "center" } };
    }
    const workbook = XLSX.utils.book_new();
    workbook.Workbook = { Views: [{ RTL: true }] };
    XLSX.utils.book_append_sheet(workbook, worksheet, "بیماران");
    XLSX.writeFile(workbook, "Patients_List.xlsx");
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl font-bold text-blue-600">در حال بارگذاری لیست بیماران...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 relative">
      <header className="mb-8 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <h1 className="text-3xl font-bold text-gray-800">لیست بیماران</h1>
        
        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto items-center">
          <div className="relative w-full sm:w-80 h-11">
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full h-full pr-10 pl-3 border border-gray-200 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
              placeholder="جستجو با نام، کد ملی یا شماره تماس..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex h-11 items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 rounded-xl font-medium transition-colors shadow-sm whitespace-nowrap"
          >
            <UserPlus className="w-5 h-5" />
            ثبت بیمار جدید
          </button>

          <button
            onClick={handleExportExcel}
            className="flex h-11 items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white px-5 rounded-xl font-medium transition-colors shadow-sm whitespace-nowrap"
          >
            <Download className="w-5 h-5" />
            خروجی اکسل
          </button>
        </div>
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="p-4 text-gray-600 font-medium text-sm">ردیف</th>
                <th className="p-4 text-gray-600 font-medium text-sm">نام و نام خانوادگی</th>
                <th className="p-4 text-gray-600 font-medium text-sm">جنسیت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">کد ملی</th>
                <th className="p-4 text-gray-600 font-medium text-sm">شماره تماس</th>
                <th className="p-4 text-gray-600 font-medium text-sm">منبع ثبت‌نام</th>
                <th className="p-4 text-gray-600 font-medium text-sm">شماره پرونده</th>
                <th className="p-4 text-gray-600 font-medium text-sm">تاریخ ثبت‌نام</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredPatients.map((patient, index) => (
                <tr key={patient.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-gray-800 font-medium">{index + 1}</td>
                  <td className="p-4 text-gray-800 font-medium">{patient.first_name} {patient.last_name}</td>
                  <td className="p-4 text-gray-600 text-sm">{genderMap[patient.gender] || "ثبت نشده"}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm">{patient.national_id || "ثبت نشده"}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">{patient.phone_number}</td>
                  <td className="p-4 text-sm font-medium">
                    <span className={patient.user_id ? "text-blue-600 bg-blue-50 px-2 py-1 rounded" : "text-gray-600 bg-gray-50 px-2 py-1 rounded"}>
                      {patient.user_id ? "ربات بله" : "پنل منشی"}
                    </span>
                  </td>
                  <td className="p-4 text-gray-500 font-mono text-sm">#{patient.id}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">
                    {formatJalaliDateTime(patient.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in p-4">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-xl overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-gray-50">
              <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-blue-600" /> تشکیل پرونده بیمار جدید
              </h3>
              <button onClick={handleCloseModal} className="text-gray-400 hover:text-red-500 transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <form onSubmit={handleCreatePatient} className="p-6 space-y-5">
              {submitError && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm font-medium">{submitError}</div>}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">کد ملی:</label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="کد ملی ۱۰ رقمی را وارد کنید..."
                    className="w-full pl-12 pr-4 h-[50px] border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-right font-mono tracking-widest placeholder:text-gray-400 placeholder:font-sans"
                    dir="rtl"
                    value={newNationalId}
                    onChange={(e) => setNewNationalId(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    required
                  />
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center justify-center">
                    {newNationalId.length === 10 ? (
                      isValidIranianNationalId(newNationalId) ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <span className="flex items-center justify-center w-6 h-6 bg-gray-100 text-gray-500 text-xs font-bold rounded-md">{10 - newNationalId.length}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">نام:</label>
                  <input type="text" value={newFirstName} onChange={e => setNewFirstName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-[50px] border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">نام خانوادگی:</label>
                  <input type="text" value={newLastName} onChange={e => setNewLastName(e.target.value.replace(/[0-9۰-۹]/g, ''))} className="w-full px-4 h-[50px] border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" required />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">شماره تماس:</label>
                  <div className="relative">
                    <input type="text" value={newPhone} onChange={e => setNewPhone(e.target.value.replace(/\D/g, '').slice(0, 11))} placeholder="09123456789" dir="ltr" className="w-full pl-10 pr-3 h-[50px] border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-center font-mono tracking-widest" required />
                    <div className="absolute left-2 top-1/2 -translate-y-1/2 flex items-center justify-center">
                      {newPhone.length === 11 ? (
                        newPhone.startsWith("09") ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />
                      ) : (
                        <span className="flex items-center justify-center w-6 h-6 bg-blue-50 text-blue-600 text-xs font-bold rounded-md">{11 - newPhone.length}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">جنسیت:</label>
                  <div className="flex bg-gray-100 p-1 rounded-xl border border-gray-200 h-[50px] items-center">
                    <button type="button" onClick={() => setNewGender('male')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all ${newGender === 'male' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>آقا</button>
                    <button type="button" onClick={() => setNewGender('female')} className={`flex-1 h-full text-sm font-bold rounded-lg transition-all ${newGender === 'female' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>خانم</button>
                  </div>
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button type="button" onClick={handleCloseModal} className="flex-1 px-4 py-3 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors">
                  انصراف
                </button>
                <button type="submit" disabled={submitLoading} className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-70">
                  {submitLoading ? "در حال ثبت‌نام..." : "ذخیره پرونده"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}