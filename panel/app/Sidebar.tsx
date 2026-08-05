"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CalendarDays, Users, Settings, LogOut } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  
  if (pathname === "/login") {
    return null;
  }

  return (
    <aside className="w-64 bg-white border-l border-gray-200 flex flex-col shadow-sm">
      <div className="h-20 flex items-center justify-center border-b border-gray-100">
        <span className="text-xl font-extrabold text-blue-600">Clinic Panel</span>
      </div>
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        <Link href="/" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-blue-600 rounded-xl font-medium transition-colors">
          <LayoutDashboard className="w-5 h-5" />
          داشبورد
        </Link>
        <Link href="/appointments" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-blue-600 rounded-xl font-medium transition-colors">
          <CalendarDays className="w-5 h-5" />
          مدیریت نوبت‌ها
        </Link>
        <Link href="/patients" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-blue-600 rounded-xl font-medium transition-colors">
          <Users className="w-5 h-5" />
          لیست بیماران
        </Link>
        <Link href="/settings" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-blue-600 rounded-xl font-medium transition-colors">
          <Settings className="w-5 h-5" />
          تنظیمات سیستم
        </Link>
      </nav>
      <div className="p-4 border-t border-gray-100">
        <Link href="/logout" className="flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl font-medium transition-colors">
          <LogOut className="w-5 h-5" />
          خروج از حساب
        </Link>
      </div>
    </aside>
  );
}