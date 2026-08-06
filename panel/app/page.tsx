"use client";

import { useEffect, useState, useCallback } from "react";
import { Users, Calendar as CalendarIcon, CheckCircle, Clock, AlertCircle, X, ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";

interface DashboardStats { total_patients: number; active_appointments: number; cancelled_appointments: number; today_appointments: number; }
interface TodayAppointment { id: number; first_name: string; last_name: string; phone_number: string; service_name: string; start_time: string; status: string; }

const toEnglishDigits = (str: string | null) => {
  if (!str) return "";
  const persianNumbers = [/۰/g, /۱/g, /۲/g, /۳/g, /۴/g, /۵/g, /۶/g, /۷/g, /۸/g, /۹/g];
  const arabicNumbers = [/٠/g, /١/g, /٢/g, /٣/g, /٤/g, /٥/g, /٦/g, /٧/g, /٨/g, /٩/g];
  let result = String(str);
  for (let i = 0; i < 10; i++) { result = result.replace(persianNumbers[i], String(i)).replace(arabicNumbers[i], String(i)); }
  return result;
};

const getPageNumbers = (current: number, total: number) => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (current <= 4) return [1, 2, 3, 4, 5, "...", total];
  if (current >= total - 3) return [1, "...", total - 4, total - 3, total - 2, total - 1, total];
  return [1, "...", current - 1, current, current + 1, "...", total];
};

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats>({ total_patients: 0, active_appointments: 0, cancelled_appointments: 0, today_appointments: 0 });
  const [todayAppointments, setTodayAppointments] = useState<TodayAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const fetchData = useCallback(async () => {
    try {
      const statsRes = await fetch("http://127.0.0.1:8000/api/dashboard/stats");
      setStats(await statsRes.json());
      const apptsRes = await fetch("http://127.0.0.1:8000/api/dashboard/today");
      const apptsData = await apptsRes.json();
      setTodayAppointments(apptsData.map((appt: TodayAppointment) => ({ ...appt, phone_number: toEnglishDigits(appt.phone_number), start_time: toEnglishDigits(appt.start_time) })));
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => { const init = async () => { await fetchData(); }; init(); }, [fetchData]);

  const handleStatusChange = async (id: number, newStatus: string) => {
    try { await fetch(`http://127.0.0.1:8000/api/appointments/${id}/status`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: newStatus }) }); fetchData(); } catch {}
  };

  const totalPages = Math.ceil(todayAppointments.length / rowsPerPage);
  const currentRows = todayAppointments.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

  if (loading) return <div className="flex h-screen items-center justify-center"><div className="text-xl font-bold text-blue-600">در حال بارگذاری داشبورد...</div></div>;

  return (
    <div className="min-h-screen px-8 w-full relative bg-gray-50">
      <header className="pt-12 pb-8 flex items-center mb-2">
        <h1 className="text-3xl font-bold text-gray-800 leading-none">داشبورد خلاصه وضعیت</h1>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          { title: "کل بیماران سیستم", val: stats.total_patients, icon: Users, bgIcon: "bg-blue-500", textColor: "text-blue-600" },
          { title: "نوبت‌های امروز", val: stats.today_appointments, icon: Clock, bgIcon: "bg-amber-500", textColor: "text-amber-600" },
          { title: "کل نوبت‌های فعال", val: stats.active_appointments, icon: CalendarIcon, bgIcon: "bg-emerald-500", textColor: "text-emerald-600" },
          { title: "نوبت‌های لغو شده", val: stats.cancelled_appointments, icon: AlertCircle, bgIcon: "bg-red-500", textColor: "text-red-600" },
        ].map((s, i) => (
          <div key={i} className="bg-white rounded-2xl p-6 shadow-sm flex items-center border border-gray-100">
            <div className={`p-4 rounded-xl ${s.bgIcon} text-white ml-5 shadow-sm`}><s.icon className="w-6 h-6" /></div>
            <div className="flex flex-col">
              <p className="text-gray-500 text-sm font-medium mb-1.5">{s.title}</p>
              <p className={`text-3xl font-bold font-mono tracking-tight ${s.textColor}`}>{s.val}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2"><Clock className="w-5 h-5 text-blue-600"/> لیست مراجعین امروز</h2>
          <button onClick={() => router.push('/appointments')} className="flex items-center gap-2 px-5 py-2.5 bg-blue-50 text-blue-600 hover:bg-blue-600 hover:text-white rounded-xl text-sm font-bold transition-all shadow-sm group cursor-pointer">
            مدیریت کل نوبت‌ها
            <ArrowLeft className="w-4 h-4 transform group-hover:-translate-x-1 transition-transform" />
          </button>
        </div>
        
        {todayAppointments.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-100 rounded-xl bg-gray-50">
            <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">امروز نوبتی در سیستم ثبت نشده است.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto rounded-xl border border-gray-100 mb-6">
              <table className="w-full text-right">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr><th className="p-4 font-medium text-gray-600 text-sm">نام بیمار</th><th className="p-4 font-medium text-gray-600 text-sm">ساعت</th><th className="p-4 font-medium text-gray-600 text-sm">شماره تماس</th><th className="p-4 font-medium text-gray-600 text-sm">خدمت درمانی</th><th className="p-4 font-medium text-gray-600 text-sm text-center">وضعیت حضور</th></tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentRows.map(a => (
                    <tr key={a.id} className="hover:bg-gray-50 transition-colors">
                      <td className="p-4 font-medium text-gray-800">{a.first_name} {a.last_name}</td>
                      <td className="p-4" dir="ltr"><span className="inline-flex items-center justify-center px-3 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 font-mono text-sm font-bold shadow-sm">{a.start_time}</span></td>
                      <td className="p-4 font-mono text-gray-600 text-sm" dir="ltr">{a.phone_number}</td>
                      <td className="p-4 text-gray-800">{a.service_name}</td>
                      <td className="p-4 flex justify-center">
                        {a.status === 'scheduled' ? (
                          <div className="flex gap-2">
                            <button onClick={() => handleStatusChange(a.id, 'accepted')} className="text-xs bg-green-50 text-green-600 font-bold px-4 py-2 rounded-lg hover:bg-green-100 transition-colors flex items-center gap-1.5 cursor-pointer"><CheckCircle className="w-4 h-4" /> حضور</button>
                            <button onClick={() => handleStatusChange(a.id, 'no_show')} className="text-xs bg-red-50 text-red-600 font-bold px-4 py-2 rounded-lg hover:bg-red-100 transition-colors flex items-center gap-1.5 cursor-pointer"><X className="w-4 h-4" /> غایب</button>
                          </div>
                        ) : (
                          <span className={`text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-1.5 w-32 justify-center shadow-sm ${a.status === 'accepted' ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-500'}`}>
                            {a.status === 'accepted' ? <><CheckCircle className="w-4 h-4" /> انجام شد</> : <><X className="w-4 h-4" /> عدم مراجعه</>}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col sm:flex-row justify-between items-center p-4 bg-white border border-gray-200 rounded-xl shadow-sm gap-4">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-600">
                <span>نمایش</span>
                <select value={rowsPerPage} onChange={(e) => { setRowsPerPage(Number(e.target.value)); setCurrentPage(1); }} className="border border-gray-200 rounded-lg px-3 py-1.5 outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 cursor-pointer">
                  {[5, 10, 25, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
                <span>ردیف در هر صفحه</span>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1} className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-200 text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors cursor-pointer"><ChevronRight className="w-5 h-5" /></button>
                <div className="flex gap-1 flex-wrap justify-center px-2">
                  {getPageNumbers(currentPage, totalPages).map((pageNum, idx) => (
                    pageNum === "..." ? <span key={idx} className="w-10 h-10 flex items-center justify-center text-gray-400 font-medium">...</span> :
                    <button key={idx} onClick={() => setCurrentPage(pageNum as number)} className={`w-10 h-10 flex items-center justify-center rounded-xl text-sm font-bold transition-all cursor-pointer ${currentPage === pageNum ? 'bg-blue-600 text-white shadow-md' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}`}>{pageNum}</button>
                  ))}
                </div>
                <button onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages || totalPages === 0} className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-200 text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors cursor-pointer"><ChevronLeft className="w-5 h-5" /></button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}