"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CalendarDays, Users, Settings, LogOut, ClipboardPlus, PieChart } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  
  if (pathname === "/login") {
    return null;
  }

  const baseClass = "flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-all duration-200 cursor-pointer";
  const activeClass = "bg-blue-600 text-white shadow-md shadow-blue-200";
  const inactiveClass = "text-gray-600 hover:bg-gray-50 hover:text-blue-600";

  return (
    <aside className="w-64 bg-white border-l border-gray-200 flex flex-col shadow-sm">
      <div className="pt-12 pb-8 flex items-center justify-center border-b border-gray-100">
        <span className="text-2xl font-extrabold bg-linear-to-r from-blue-700 to-blue-500 bg-clip-text text-transparent leading-none">
          Clinic Panel
        </span>
      </div>
      
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        <Link href="/" className={`${baseClass} ${pathname === '/' ? activeClass : inactiveClass}`}>
          <LayoutDashboard className="w-5 h-5" />
          داشبورد
        </Link>
        <Link href="/desk" className={`${baseClass} ${pathname === '/desk' ? activeClass : inactiveClass}`}>
          <ClipboardPlus className="w-5 h-5" />
          میز کار منشی
        </Link>
        <Link href="/appointments" className={`${baseClass} ${pathname === '/appointments' ? activeClass : inactiveClass}`}>
          <CalendarDays className="w-5 h-5" />
          مدیریت نوبت‌ها
        </Link>
        <Link href="/patients" className={`${baseClass} ${pathname === '/patients' ? activeClass : inactiveClass}`}>
          <Users className="w-5 h-5" />
          لیست بیماران
        </Link>
        
        <div className="pt-4 pb-2">
          <p className="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider">مدیریت و تحلیل</p>
        </div>
        
        <Link href="/reports" className={`${baseClass} ${pathname === '/reports' ? activeClass : inactiveClass}`}>
          <PieChart className="w-5 h-5" />
          گزارش‌ها و آمار
        </Link>
        <Link href="/settings" className={`${baseClass} ${pathname === '/settings' ? activeClass : inactiveClass}`}>
          <Settings className="w-5 h-5" />
          تنظیمات سیستم
        </Link>
      </nav>
      
      <div className="p-4 border-t border-gray-100">
        <Link href="/logout" className="flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl font-bold transition-colors cursor-pointer">
          <LogOut className="w-5 h-5" />
          خروج از حساب
        </Link>
      </div>
    </aside>
  );
}