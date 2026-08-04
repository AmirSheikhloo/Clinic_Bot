"use client";

import { useEffect, useState } from "react";

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
        const apptData = await apptRes.json();
        setAppointments(apptData);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">کل پرونده‌ها</h3>
          <p className="text-3xl font-bold text-gray-800">{stats?.total_patients || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">نوبت‌های فعال</h3>
          <p className="text-3xl font-bold text-blue-600">{stats?.active_appointments || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">نوبت‌های لغوشده</h3>
          <p className="text-3xl font-bold text-red-500">{stats?.cancelled_appointments || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 transition-all hover:shadow-md">
          <h3 className="text-gray-500 text-sm font-medium mb-2">خدمات فعال</h3>
          <p className="text-3xl font-bold text-green-600">{stats?.active_services || 0}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-800">لیست آخرین نوبت‌ها</h2>
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
              {appointments.map((appt) => (
                <tr key={appt.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-gray-800 font-medium">{appt.first_name} {appt.last_name}</td>
                  <td className="p-4 text-gray-600">{appt.national_id}</td>
                  <td className="p-4 text-gray-600" dir="ltr">{appt.phone_number}</td>
                  <td className="p-4 text-gray-800">{appt.service_name}</td>
                  <td className="p-4 text-gray-600">{appt.appointment_date} | {appt.start_time}</td>
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