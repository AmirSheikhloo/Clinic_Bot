"use client";

import { useState, useEffect } from "react";
import { Check, X } from "lucide-react";

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

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0); // استیت جدید برای رفرش کردن جدول

  useEffect(() => {
    // تابع فچ کردن دیتا دقیقاً داخل useEffect تعریف می‌شود تا ارور ESLint برطرف شود
    const fetchAppointments = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/appointments");
        const data = await res.json();
        setAppointments(data);
      } catch (error) {
        console.error("Error fetching appointments:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, [refreshTrigger]); // هر بار این مقدار تغییر کند، لیست نوبت‌ها دوباره از سرور گرفته می‌شود

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/appointments/${id}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.ok) {
        // به جای صدا زدن تابع، فقط تریگر را تغییر می‌دهیم تا جدول خودش آپدیت شود
        setRefreshTrigger(prev => prev + 1);
      }
    } catch (error) {
      console.error("Error updating status:", error);
    }
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
      <header className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">مدیریت نوبت‌ها</h1>
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="p-4 text-gray-600 font-medium text-sm">بیمار</th>
                <th className="p-4 text-gray-600 font-medium text-sm">شماره تماس</th>
                <th className="p-4 text-gray-600 font-medium text-sm">خدمت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">تاریخ و ساعت</th>
                <th className="p-4 text-gray-600 font-medium text-sm">وضعیت</th>
                <th className="p-4 text-gray-600 font-medium text-sm text-center">عملیات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {appointments.map((appt) => (
                <tr key={appt.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-gray-800 font-medium">{appt.first_name} {appt.last_name}</td>
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
              {appointments.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-500">هیچ نوبتی یافت نشد.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}