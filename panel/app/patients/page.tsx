"use client";

import { useState, useEffect } from "react";
import { Search, Download } from "lucide-react";
import * as XLSX from "xlsx-js-style";

interface Patient {
  id: number;
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

const insuranceMap: Record<string, string> = {
  health: "سلامت",
  social_security: "تأمین اجتماعی",
  armed_forces: "نیروهای مسلح",
  none: "بدون بیمه"
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

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/patients");
        const data: Patient[] = await res.json();
        
        const formattedData = data
          .sort((a, b) => a.id - b.id)
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

    fetchPatients();
  }, []);

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
      "شماره پرونده": p.id,
      "نام و نام خانوادگی": `${p.first_name} ${p.last_name}`,
      "کد ملی": p.national_id || "ثبت نشده",
      "شماره تماس": p.phone_number,
      "جنسیت": genderMap[p.gender] || p.gender || "نامشخص",
      "بیمه": insuranceMap[p.insurance] || p.insurance || "نامشخص",
      "تاریخ و ساعت ثبت‌نام": formatJalaliDateTime(p.created_at)
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    
    worksheet['!cols'] = [
      { wch: 8 }, { wch: 15 }, { wch: 25 }, { wch: 15 }, 
      { wch: 15 }, { wch: 10 }, { wch: 15 }, { wch: 25 }
    ];

    for (const i in worksheet) {
      if (typeof worksheet[i] !== 'object') continue;
      worksheet[i].s = {
        alignment: { horizontal: "center", vertical: "center" }
      };
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
    <div className="min-h-screen p-8">
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
                <th className="p-4 text-gray-600 font-medium text-sm">شماره پرونده</th>
                <th className="p-4 text-gray-600 font-medium text-sm">نام و نام خانوادگی</th>
                <th className="p-4 text-gray-600 font-medium text-sm">کد ملی</th>
                <th className="p-4 text-gray-600 font-medium text-sm">شماره تماس</th>
                <th className="p-4 text-gray-600 font-medium text-sm">تاریخ ثبت‌نام</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredPatients.map((patient, index) => (
                <tr key={patient.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-gray-800 font-medium">{index + 1}</td>
                  <td className="p-4 text-gray-500 font-mono text-sm">#{patient.id}</td>
                  <td className="p-4 text-gray-800 font-medium">{patient.first_name} {patient.last_name}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm">{patient.national_id || "ثبت نشده"}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">{patient.phone_number}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">
                    {formatJalaliDateTime(patient.created_at)}
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