"use client";

import { useEffect, useState, useCallback } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp, Activity, Users, ListOrdered, CalendarDays, Lock, CreditCard } from "lucide-react";

interface ReportStats {
  success_rate: number;
  popular_service: string;
  total_appointments: number;
  pending_appointments: number;
  services_performance: {
    name: string;
    total: number;
    completed: number;
    pending: number;
    cancelled: number;
    no_show: number;
  }[];
}

export default function ReportsPage() {
  const [stats, setStats] = useState<ReportStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/reports/stats");
      setStats(await res.json());
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      await fetchData();
    };
    init();
  }, [fetchData]);

  const getChartData = () => {
    if (!stats) return [];
    return stats.services_performance.map((s) => ({
      name: s.name.replace(' آقایان', '').replace(' بانوان', ''),
      count: s.total,
    }));
  };

  if (loading) return <div className="flex h-screen items-center justify-center"><div className="text-xl font-bold text-blue-600">در حال پردازش آمار...</div></div>;

  return (
    <div className="min-h-screen px-8 pt-10 pb-8 w-full relative bg-gray-50">
      <header className="flex items-center justify-between mb-8 border-b-transparent">
        <h1 className="text-3xl font-bold text-gray-800 leading-none">گزارش‌ها و تحلیل آمار</h1>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="p-4 bg-emerald-50 rounded-xl"><TrendingUp className="w-8 h-8 text-emerald-600" /></div>
          <div><p className="text-gray-500 text-sm font-bold mb-1">نرخ موفقیت کل</p><p className="text-3xl font-black font-mono text-gray-800">{stats?.success_rate}%</p></div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="p-4 bg-purple-50 rounded-xl"><Users className="w-8 h-8 text-purple-600" /></div>
          <div><p className="text-gray-500 text-sm font-bold mb-1">کل پردازش شده</p><p className="text-3xl font-black font-mono text-gray-800">{stats?.total_appointments}</p></div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="p-4 bg-amber-50 rounded-xl"><CalendarDays className="w-8 h-8 text-amber-600" /></div>
          <div><p className="text-gray-500 text-sm font-bold mb-1">در انتظار (آینده)</p><p className="text-3xl font-black font-mono text-gray-800">{stats?.pending_appointments}</p></div>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4">
          <div className="p-4 bg-blue-50 rounded-xl"><Activity className="w-8 h-8 text-blue-600" /></div>
          <div className="overflow-hidden"><p className="text-gray-500 text-sm font-bold mb-1">محبوب‌ترین</p><p className="text-lg font-black text-gray-800 truncate">{stats?.popular_service || "---"}</p></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-bold text-gray-800 mb-8 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" /> پراکندگی درخواست خدمات
          </h2>
          <div className="h-80 w-full" dir="ltr">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={getChartData()} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12, fontWeight: 'bold' }} axisLine={false} tickLine={false} angle={-45} textAnchor="end" />
                <YAxis allowDecimals={false} tick={{ fill: '#6b7280', fontSize: 12, fontWeight: 'bold' }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} maxBarSize={50} name="تعداد رزرو" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col">
          <h2 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
            <ListOrdered className="w-5 h-5 text-blue-600" /> جدول عملکرد خدمات
          </h2>
          <div className="overflow-x-auto rounded-xl border border-gray-100 flex-1">
            <table className="w-full text-right">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="p-4 font-bold text-gray-600 text-sm">نام خدمت</th>
                  <th className="p-4 font-bold text-gray-600 text-sm text-center">کل نوبت‌ها</th>
                  <th className="p-4 font-bold text-emerald-600 text-sm text-center">موفق</th>
                  <th className="p-4 font-bold text-amber-600 text-sm text-center">آینده</th>
                  <th className="p-4 font-bold text-red-600 text-sm text-center">لغو شده</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {stats?.services_performance.map((s, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4 font-bold text-gray-800 text-sm">{s.name}</td>
                    <td className="p-4 text-center font-mono font-bold text-gray-700">{s.total}</td>
                    <td className="p-4 text-center font-mono font-bold text-emerald-600 bg-emerald-50/50">{s.completed}</td>
                    <td className="p-4 text-center font-mono font-bold text-amber-600 bg-amber-50/50">{s.pending}</td>
                    <td className="p-4 text-center font-mono font-bold text-red-500 bg-red-50/50">{s.cancelled}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="relative rounded-2xl overflow-hidden border border-gray-200 mb-8">
        <div className="absolute inset-0 bg-white/70 backdrop-blur-md z-10 flex flex-col items-center justify-center">
          <div className="bg-white p-4 rounded-full shadow-lg mb-4">
            <Lock className="w-8 h-8 text-blue-600" />
          </div>
          <h3 className="text-2xl font-black text-gray-800 mb-2">داشبورد حسابداری و مالی</h3>
          <p className="text-gray-600 font-bold text-sm bg-white/80 px-4 py-2 rounded-lg">این بخش در فازهای بعدی توسعه در دسترس قرار می‌گیرد.</p>
        </div>
        
        <div className="bg-white p-8 opacity-40 select-none">
          <h2 className="text-xl font-bold text-gray-800 mb-8 flex items-center gap-2"><CreditCard className="w-6 h-6"/> تراکنش‌ها و درآمدها</h2>
          <div className="grid grid-cols-3 gap-6 mb-8">
            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
              <p className="text-slate-500 font-bold">درآمد امروز</p><p className="text-3xl font-mono font-black mt-2">14,500,000 <span className="text-sm">تومان</span></p>
            </div>
            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
              <p className="text-slate-500 font-bold">درآمد این ماه</p><p className="text-3xl font-mono font-black mt-2">240,000,000 <span className="text-sm">تومان</span></p>
            </div>
            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
              <p className="text-slate-500 font-bold">تسویه‌نشده</p><p className="text-3xl font-mono font-black mt-2 text-red-500">2,500,000 <span className="text-sm">تومان</span></p>
            </div>
          </div>
          <div className="h-48 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-center">
            <p className="font-mono text-slate-300 text-3xl font-black">CHART PREVIEW</p>
          </div>
        </div>
      </div>
    </div>
  );
}