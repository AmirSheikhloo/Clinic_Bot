import type { Metadata } from "next";
import { Vazirmatn } from "next/font/google";
import Sidebar from "./Sidebar";
import "./globals.css";

const vazirmatn = Vazirmatn({ 
  subsets: ["arabic", "latin"],
  variable: "--font-vazirmatn",
  display: "swap",
});

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
    <html lang="fa" dir="rtl" className={vazirmatn.variable}>
      <body suppressHydrationWarning className="font-sans bg-gray-50 text-gray-900 antialiased flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}