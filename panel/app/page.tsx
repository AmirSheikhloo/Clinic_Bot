"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface Stats {
  total_patients: number;
  active_appointments: number;
  cancelled_appointments: number;
  active_services: number;
}

interface Appointment {
  id: number;
  first_name: string;
  last_name: string;
  national_id: string;
  phone_number: string;
  service_name: string;
  appointment_date: string;
  start_time: string;
  status: string;
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

const formatJalaliDate = (dateString: string) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("fa-IR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    numberingSystem: "latn",
  }).format(date);
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsRes = await fetch("http://127.0.0.1:8000/api/dashboard/stats");
        const statsData = await statsRes.json();
        setStats(statsData);

        const apptRes = await fetch("http://127.0.0.1:8000/api/appointments");
        const apptData: Appointment[] = await apptRes.json();
        
        const formattedAppts = apptData.map((appt: Appointment) => ({
          ...appt,
          national_id: toEnglishDigits(appt.national_id),
          phone_number: toEnglishDigits(appt.phone_number),
          start_time: toEnglishDigits(appt.start_time),
          appointment_date: formatJalaliDate(appt.appointment_date)
        }));
        
        setAppointments(formattedAppts);
      } catch {
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getChartData = () => {
    const counts: Record<string, number> = {};
    appointments.forEach((appt) => {
      counts[appt.service_name] = (counts[appt.service_name] || 0) + 1;
    });
    return Object.keys(counts).map((key) => ({
      name: key,
      count: counts[key],
    }));
  };

  const chartData = getChartData();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl font-bold text-blue-600">در حال دریافت اطلاعات از سرور...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">داشبورد مدیریت درمانگاه</h1>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">کل پرونده‌ها</h3>
          <p className="text-3xl font-bold text-gray-800 font-mono">{stats?.total_patients || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">نوبت‌های فعال</h3>
          <p className="text-3xl font-bold text-blue-600 font-mono">{stats?.active_appointments || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">نوبت‌های لغوشده</h3>
          <p className="text-3xl font-bold text-red-500 font-mono">{stats?.cancelled_appointments || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">خدمات فعال</h3>
          <p className="text-3xl font-bold text-green-600 font-mono">{stats?.active_services || 0}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-8 p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-6">آمار نوبت‌ها به تفکیک خدمات</h2>
        <div className="h-72 w-full" dir="ltr">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip 
                formatter={(value) => [value, 'تعداد']}
                cursor={{ fill: '#f9fafb' }}
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={50} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">لیست آخرین نوبت‌ها</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-4 text-gray-600 font-medium text-sm">بیمار</th>
                <th className="p-4 text-gray-600 font-medium text-sm">کد ملی</th>
                <th className="p-4 text-gray-600 font-medium text-sm">شماره تماس</th>
                <th className="p-4 text-gray-600 font-medium text-sm">خدمت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">تاریخ و ساعت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">وضعیت</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {appointments.slice(0, 5).map((appt) => (
                <tr key={appt.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-gray-800 font-medium">{appt.first_name} {appt.last_name}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm">{appt.national_id || "ثبت نشده"}</td>
                  <td className="p-4 text-gray-600 font-mono text-sm" dir="ltr">{appt.phone_number}</td>
                  <td className="p-4 text-gray-800">{appt.service_name}</td>
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
                       appt.status === 'cancelled' ? 'لغو شده' : appt.status}
                    </span>
                  </td>
                </tr>
              ))}
              {appointments.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-500">هیچ نوبتی در سیستم ثبت نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}