import type { Metadata } from "next";
import Link from "next/link";
import { LayoutDashboard, CalendarDays, Users, Settings } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "پنل مدیریت درمانگاه",
  description: "سیستم مدیریت نوبت‌دهی درمانگاه",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body suppressHydrationWarning className="bg-gray-50 text-gray-900 font-sans antialiased flex h-screen overflow-hidden">
        
        <aside className="w-64 bg-white border-l border-gray-200 flex flex-col shadow-sm">
          <div className="h-20 flex items-center justify-center border-b border-gray-100">
            <span className="text-xl font-extrabold text-blue-600">Clinic Panel</span>
          </div>
          
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            <Link href="/" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-xl font-medium transition-colors">
              <LayoutDashboard className="w-5 h-5" />
              داشبورد
            </Link>
            
            <Link href="/appointments" className="flex items-center gap-3 px-4 py-3 text-blue-700 bg-blue-50 rounded-xl font-medium transition-colors">
              <CalendarDays className="w-5 h-5" />
              مدیریت نوبت‌ها
            </Link>
            
            <Link href="/patients" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-xl font-medium transition-colors">
              <Users className="w-5 h-5" />
              لیست بیماران
            </Link>
            
            <Link href="/settings" className="flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-xl font-medium transition-colors">
              <Settings className="w-5 h-5" />
              تنظیمات سیستم
            </Link>
          </nav>
        </aside>

        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
        
      </body>
    </html>
  );
}