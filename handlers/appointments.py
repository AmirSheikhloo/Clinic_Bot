"use client";

import { useState, useEffect } from "react";
import { Check, X, Search, Download } from "lucide-react";
import * as XLSX from "xlsx-js-style";

interface Appointment {
  id: number;
  user_id?: number | null;
  source?: string;
  first_name: string;
  last_name: string;
  national_id: string;
  phone_number: string;
  service_name: string;
  appointment_date: string;
  start_time: string;
  status: string;
  created_at: string;
  gender?: string;
}

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

const formatTrackingCode = (id: number) => {
  return `CF-${String(id).padStart(6, '0')}`;
};

// تابع هوشمند تشخیص و چسباندن جنسیت به خدمات خاص
const getServiceDisplayName = (serviceName: string, gender?: string) => {
  if (!serviceName) return "";
  let display = serviceName;
  const genderedServices = ["بادکش", "حجامت عام", "زالودرمانی"];
  const isGendered = genderedServices.some(s => display.includes(s));

  if (isGendered) {
    if (gender === "male") display += " آقایان";
    else if (gender === "female") display += " بانوان";
  }
  return display;
};

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/appointments");
        const data: Appointment[] = await res.json();
        
        const formattedData = data.map(appt => ({
          ...appt,
          national_id: toEnglishDigits(appt.national_id),
          phone_number: toEnglishDigits(appt.phone_number),
          start_time: toEnglishDigits(appt.start_time)
        }));
        
        setAppointments(formattedData);
      } catch {
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, [refreshTrigger]);

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/appointments/${id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.ok) {
        setRefreshTrigger(prev => prev + 1);
      }
    } catch {}
  };

  const query = toEnglishDigits(searchQuery.trim().toLowerCase());
  
  const filteredAppointments = query
    ? appointments.filter((a) => {
        const trackingCode = formatTrackingCode(a.id).toLowerCase();
        const displayService = getServiceDisplayName(a.service_name, a.gender).toLowerCase();
        return (
          trackingCode.includes(query) ||
          a.id.toString() === query ||
          a.first_name.includes(query) ||
          a.last_name.includes(query) ||
          (a.national_id && a.national_id.includes(query)) ||
          (a.phone_number && a.phone_number.includes(query)) ||
          displayService.includes(query)
        );
      })
    : appointments;

  const handleExportExcel = () => {
    const exportData = filteredAppointments.map((a, index) => ({
      "ردیف": index + 1,
      "نام و نام خانوادگی": `${a.first_name} ${a.last_name}`,
      "کد ملی": a.national_id || "ثبت نشده",
      "شماره تماس": a.phone_number,
      "خدمت": getServiceDisplayName(a.service_name, a.gender),
      "تاریخ مراجعه": a.appointment_date,
      "ساعت مراجعه": a.start_time,
      "وضعیت": a.status === 'scheduled' ? 'در انتظار' : 
               a.status === 'accepted' ? 'پذیرش شده' : 
               a.status === 'cancelled' ? 'لغو شده' : 
               a.status === 'no_show' ? 'عدم مراجعه' : a.status,
      "منبع دریافت نوبت": a.source === 'panel' ? "پنل مدیریت (توسط منشی)" : "ربات بله / تلگرام",
      "کد پیگیری": formatTrackingCode(a.id),
      "زمان ثبت نوبت در سیستم": formatJalaliDateTime(a.created_at)
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    
    worksheet['!cols'] = [
      { wch: 8 }, { wch: 25 }, { wch: 15 }, { wch: 15 }, 
      { wch: 25 }, { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 25 }, { wch: 15 }, { wch: 25 }
    ];

    for (const i in worksheet) {
      if (typeof worksheet[i] !== 'object') continue;
      worksheet[i].s = {
        alignment: { horizontal: "center", vertical: "center" }
      };
    }

    const workbook = XLSX.utils.book_new();
    workbook.Workbook = { Views: [{ RTL: true }] };
    XLSX.utils.book_append_sheet(workbook, worksheet, "نوبت‌ها");
    XLSX.writeFile(workbook, "Appointments_List.xlsx");
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl font-bold text-blue-600">در حال بارگذاری نوبت‌ها...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <h1 className="text-3xl font-bold text-gray-800">مدیریت نوبت‌ها</h1>
        
        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto items-center">
          <div className="relative w-full sm:w-80 h-11">
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full h-full pr-10 pl-3 border border-gray-200 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
              placeholder="جستجوی کد پیگیری، بیمار، خدمت..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
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
                <th className="p-4 text-gray-600 font-medium text-sm">کد پیگیری</th>
                <th className="p-4 text-gray-600 font-medium text-sm">بیمار</th>
                <th className="p-4 text-gray-600 font-medium text-sm">شماره تماس</th>
                <th className="p-4 text-gray-600 font-medium text-sm">منبع</th>
                <th className="p-4 text-gray-600 font-medium text-sm">خدمت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">تاریخ و ساعت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">وضعیت</th>
                <th className="p-4 text-gray-600 font-medium text-sm text-center">عملیات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredAppointments.map((appt) => (
                <tr key={appt.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-blue-600 font-mono font-medium text-sm bg-blue-50/30">{formatTrackingCode(appt.id)}</td>
                  <td className="p-4 text-gray-800 font-medium">{appt.first_name} {appt.last_name}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">{appt.phone_number}</td>
                  <td className="p-4 text-sm font-medium">
                    <span className={appt.source === 'panel' ? "text-gray-600 bg-gray-50 px-2 py-1 rounded" : "text-blue-600 bg-blue-50 px-2 py-1 rounded"}>
                      {appt.source === 'panel' ? "پنل منشی" : "ربات بله"}
                    </span>
                  </td>
                  <td className="p-4 text-gray-800">{getServiceDisplayName(appt.service_name, appt.gender)}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm">{appt.appointment_date} | {appt.start_time}</td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      appt.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                      appt.status === 'accepted' ? 'bg-green-100 text-green-700' :
                      appt.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {appt.status === 'scheduled' ? 'در انتظار' : 
                       appt.status === 'accepted' ? 'پذیرش شده' : 
                       appt.status === 'cancelled' ? 'لغو شده' : 
                       appt.status === 'no_show' ? 'عدم مراجعه' : appt.status}
                    </span>
                  </td>
                  <td className="p-4 flex justify-center gap-2">
                    {appt.status === 'scheduled' && (
                      <>
                        <button 
                          onClick={() => handleStatusChange(appt.id, 'accepted')}
                          className="flex items-center gap-1 bg-green-50 text-green-600 hover:bg-green-100 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                        >
                          <Check className="w-4 h-4" /> پذیرش
                        </button>
                        <button 
                          onClick={() => handleStatusChange(appt.id, 'cancelled')}
                          className="flex items-center gap-1 bg-red-50 text-red-600 hover:bg-red-100 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                        >
                          <X className="w-4 h-4" /> لغو
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}