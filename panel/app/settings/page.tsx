"use client";

import { useState, useEffect } from "react";
import { Save } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    clinic_name: "",
    clinic_phone: "",
    clinic_address: "",
    working_hours: "",
  });
  const [loading, setLoading] = useState(true);
  const [savingMessage, setSavingMessage] = useState("");

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/settings");
        const data = await res.json();
        setSettings({
          clinic_name: data.clinic_name || "",
          clinic_phone: data.clinic_phone || "",
          clinic_address: data.clinic_address || "",
          working_hours: data.working_hours || "",
        });
      } catch (error) {
        console.error("Error fetching settings:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setSettings({ ...settings, [e.target.name]: e.target.value });
  };

  const handleSave = async (key: string, value: string) => {
    setSavingMessage("در حال ذخیره...");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
      });
      if (res.ok) {
        setSavingMessage("با موفقیت ذخیره شد!");
        setTimeout(() => setSavingMessage(""), 3000);
      }
    } catch (error) {
      setSavingMessage("خطا در ذخیره‌سازی!");
      setTimeout(() => setSavingMessage(""), 3000);
    }
  };

  const handleSaveAll = async () => {
    await handleSave("clinic_name", settings.clinic_name);
    await handleSave("clinic_phone", settings.clinic_phone);
    await handleSave("clinic_address", settings.clinic_address);
    await handleSave("working_hours", settings.working_hours);
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl font-bold text-blue-600">در حال بارگذاری تنظیمات...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">تنظیمات سیستم</h1>
        {savingMessage && (
          <span className={`px-4 py-2 rounded-lg text-sm font-medium ${savingMessage.includes('خطا') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {savingMessage}
          </span>
        )}
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden max-w-3xl">
        <div className="p-6 space-y-6">
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">نام درمانگاه</label>
            <input
              type="text"
              name="clinic_name"
              value={settings.clinic_name}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="مثال: درمانگاه طب سنتی"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">شماره‌های تماس (نمایش در ربات)</label>
            <input
              type="text"
              name="clinic_phone"
              value={settings.clinic_phone}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="مثال: 02146292250"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ساعات و روزهای کاری</label>
            <input
              type="text"
              name="working_hours"
              value={settings.working_hours}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              placeholder="مثال: همه‌روزه به جز جمعه‌ها"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">آدرس دقیق درمانگاه</label>
            <textarea
              name="clinic_address"
              value={settings.clinic_address}
              onChange={handleChange}
              rows={3}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all resize-none"
              placeholder="آدرس کامل جهت نمایش به بیماران در ربات..."
            />
          </div>

          <div className="pt-4 border-t border-gray-100 flex justify-end">
            <button
              onClick={handleSaveAll}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-colors shadow-sm"
            >
              <Save className="w-5 h-5" />
              ذخیره تمام تنظیمات
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}