"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Save, Plus, X, Store, Stethoscope, Clock, Trash2, CalendarDays, AlertCircle, Edit, CheckCircle, Search, ChevronRight, ChevronLeft, History, GripVertical, RotateCcw } from "lucide-react";
import DatePicker, { DateObject } from "react-multi-date-picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import gregorian from "react-date-object/calendars/gregorian";
import gregorian_en from "react-date-object/locales/gregorian_en";

const custom_fa = { ...persian_fa, digits: ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] };
const weekDaysMap = [ { id: 5, label: "شنبه" }, { id: 6, label: "یک‌شنبه" }, { id: 0, label: "دوشنبه" }, { id: 1, label: "سه‌شنبه" }, { id: 2, label: "چهارشنبه" }, { id: 3, label: "پنج‌شنبه" }, { id: 4, label: "جمعه" } ];

interface Service { id: number; name: string; is_active: number; price: number; has_gender: number; order_index: number; }
interface ScheduleConfig { working_days: number[]; booking_days_ahead: number; default_times: Record<string, Record<string, string[]>>; weekly_times: Record<string, Record<string, Record<string, string[]>>>; }
interface ConfirmModalState { isOpen: boolean; title: string; message: string; type: 'danger' | 'warning' | 'success'; onConfirm: () => void; showCancel?: boolean; }
interface OverriddenDate { date: string; service_id: number; service_name: string; has_gender: number; slots: { time: string, gender: string }[]; }
interface HistoryLog { id: number; target_date: string; service_id: number; service_name: string; status_msg: string; details: string; logged_at: string; slots: { time: string, gender: string }[]; has_gender?: number; }

const toEnglishDigits = (str: string) => {
  const persianNumbers = [/۰/g, /۱/g, /۲/g, /۳/g, /۴/g, /۵/g, /۶/g, /۷/g, /۸/g, /۹/g];
  let result = str;
  for (let i = 0; i < 10; i++) { result = result.replace(persianNumbers[i], String(i)); }
  return result;
};

const getPageNumbers = (current: number, total: number) => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (current <= 4) return [1, 2, 3, 4, 5, "...", total];
  if (current >= total - 3) return [1, "...", total - 4, total - 3, total - 2, total - 1, total];
  return [1, "...", current - 1, current, current + 1, "...", total];
};

const CustomSelect = ({ value, options, onChange, placeholder = "انتخاب کنید...", disabled = false, grid = false }: { value: string, options: {value: string, label: string}[], onChange: (val: string) => void, placeholder?: string, disabled?: boolean, grid?: boolean }) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false); };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const selectedOption = options.find(o => o.value === value);

  return (
    <div className="relative w-full" ref={ref}>
      <div onClick={() => !disabled && setIsOpen(!isOpen)} 
           className={`w-full px-4 h-12 border rounded-xl flex items-center justify-between shadow-sm transition-all ${disabled ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed' : 'bg-white border-gray-200 cursor-pointer hover:border-blue-400 focus:ring-2 focus:ring-blue-500'}`}>
        <span className={`font-bold text-sm truncate ${selectedOption ? 'text-gray-700' : 'text-gray-400'}`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronLeft className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? '-rotate-90' : ''}`} />
      </div>
      {isOpen && !disabled && (
        <div className="absolute z-50 mt-2 w-full min-w-max bg-white border border-gray-100 rounded-xl shadow-xl overflow-hidden p-2 right-0 origin-top animate-fade-in">
          <div className={`max-h-64 overflow-y-auto ${grid && options.length > 5 ? 'grid grid-cols-1 sm:grid-cols-2 gap-1' : 'flex flex-col gap-1'}`}>
            {options.map((opt) => (
              <div key={opt.value} onClick={() => { onChange(opt.value); setIsOpen(false); }}
                   className={`px-3 py-2.5 rounded-lg font-bold text-sm cursor-pointer transition-colors flex items-center gap-2 ${value === opt.value ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'}`}>
                {value === opt.value ? <CheckCircle className="w-4 h-4 text-blue-600 shrink-0"/> : <div className="w-4 h-4 shrink-0"/>}
                <span className="truncate">{opt.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const TimeInput = ({ value, onChange, onEnter }: { value: string, onChange: (val: string) => void, onEnter: () => void }) => {
  const [h, m] = (value || "00:00").split(":");
  const minuteRef = useRef<HTMLInputElement>(null);
  const handleHourChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, '');
    if (!val) { onChange(`:${m}`); return; }
    if (val.length > 2) val = val.slice(-2);
    if (val === "24") val = "00"; else if (parseInt(val) > 23) val = val.slice(-1);
    if (val.length === 1 && parseInt(val) >= 3) val = '0' + val;
    onChange(`${val}:${m}`);
    if (val.length === 2) minuteRef.current?.focus();
  };
  const handleMinuteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, '');
    if (!val) { onChange(`${h}:`); return; }
    if (val.length > 2) val = val.slice(-2);
    if (parseInt(val) > 59) val = val.slice(-1);
    if (val.length === 1 && parseInt(val) >= 6) val = '0' + val;
    onChange(`${h}:${val}`);
  };
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => { if (e.key === 'Enter') { e.preventDefault(); onEnter(); } };
  return (
    <div className="flex items-center justify-center w-32 px-2 h-12 border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-500 bg-white transition-all shadow-sm" dir="ltr">
      <input type="tel" value={h} onChange={handleHourChange} onKeyDown={handleKeyDown} className="w-8 text-center font-mono text-lg outline-none bg-transparent" placeholder="00" />
      <span className="font-extrabold text-gray-400 mx-1">:</span>
      <input ref={minuteRef} type="tel" value={m} onChange={handleMinuteChange} onKeyDown={handleKeyDown} className="w-8 text-center font-mono text-lg outline-none bg-transparent" placeholder="00" />
    </div>
  );
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'general' | 'services' | 'schedule'>('general');
  const [scheduleSubTab, setScheduleSubTab] = useState<'defaults' | 'overrides'>('defaults');
  const [overrideListMode, setOverrideListMode] = useState<'future' | 'history'>('future');
  
  const [settings, setSettings] = useState({ clinic_name: "", clinic_address: "", working_hours_text: "" });
  const [phones, setPhones] = useState<string[]>([""]);
  
  const [services, setServices] = useState<Service[]>([]);
  const [editServiceId, setEditServiceId] = useState<number | null>(null);
  const [newServiceName, setNewServiceName] = useState("");
  const [newServicePrice, setNewServicePrice] = useState("");
  const [newServiceGender, setNewServiceGender] = useState<number>(0);
  
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({ working_days: [5,6,0,1,2,3], booking_days_ahead: 7, default_times: {}, weekly_times: {} });
  
  const [selectedServiceId, setSelectedServiceId] = useState("");
  const [selectedGender, setSelectedGender] = useState("both");
  const [targetDay, setTargetDay] = useState("all");
  
  const [newDefaultTime, setNewDefaultTime] = useState("14:00");
  const [newOverrideTime, setNewOverrideTime] = useState("14:00");
  
  const [overrideDateObj, setOverrideDateObj] = useState<DateObject>(new DateObject({ calendar: persian, locale: custom_fa }));
  const [overrideSlots, setOverrideSlots] = useState<{time: string, gender: string}[]>([]);
  const [bulkSelected, setBulkSelected] = useState<string[]>([]);
  
  const [activeOverrides, setActiveOverrides] = useState<OverriddenDate[]>([]);
  const [historyLogs, setHistoryLogs] = useState<HistoryLog[]>([]);
  
  const [overrideSearchQuery, setOverrideSearchQuery] = useState("");
  const [overrideCurrentPage, setOverrideCurrentPage] = useState(1);
  const [overrideRowsPerPage, setOverrideRowsPerPage] = useState(5);

  const [loading, setLoading] = useState(true);
  const [confirmModal, setConfirmModal] = useState<ConfirmModalState | null>(null);
  const [draggedServiceIndex, setDraggedServiceIndex] = useState<number | null>(null);

  const fetchOverrideList = useCallback(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/schedule/overrides/list");
      const data = await res.json();
      setActiveOverrides(data.active || []);
      setHistoryLogs(data.history || []);
    } catch {}
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const resSet = await fetch("http://127.0.0.1:8000/api/settings");
      const dataSet = await resSet.json();
      setSettings({ clinic_name: dataSet.clinic_name || "", clinic_address: dataSet.clinic_address || "", working_hours_text: dataSet.working_hours_text || "" });
      
      const phoneData = dataSet.clinic_phone || "";
      let parsedPhones = [""];
      if (phoneData.includes("یا")) {
        parsedPhones = phoneData.split("یا").map((p: string) => p.trim().replace(/\D/g, ''));
        if (parsedPhones[0]?.includes("462")) parsedPhones.reverse();
      } else if (phoneData.startsWith("[")) {
        try { parsedPhones = JSON.parse(phoneData); } catch {}
      } else { parsedPhones = [phoneData.replace(/\D/g, '')]; }
      setPhones(parsedPhones.filter(Boolean).length ? parsedPhones.filter(Boolean) : [""]);

      const resServ = await fetch("http://127.0.0.1:8000/api/services/all"); 
      const servicesData: Service[] = await resServ.json();
      setServices(servicesData);

      const resSched = await fetch("http://127.0.0.1:8000/api/settings/schedule");
      const schedData = await resSched.json();
      if (schedData && Object.keys(schedData).length > 0) {
        setScheduleConfig({
          working_days: schedData.working_days || [5,6,0,1,2,3],
          booking_days_ahead: schedData.booking_days_ahead || 7,
          default_times: schedData.default_times || {},
          weekly_times: schedData.weekly_times || {}
        });
      }

      const allBulk = servicesData.flatMap(s => s.has_gender === 1 ? [`${s.id}-male`, `${s.id}-female`] : [`${s.id}-all`]);
      setBulkSelected(allBulk);

      fetchOverrideList();
    } catch {
    } finally { setLoading(false); }
  }, [fetchOverrideList]);

  useEffect(() => { const init = async () => { await fetchData(); }; init(); }, [fetchData]);

  const handleSettingChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => { setSettings({ ...settings, [e.target.name]: e.target.value }); };
  const handlePhoneChange = (index: number, val: string) => { const newP = [...phones]; newP[index] = val.replace(/\D/g, ''); setPhones(newP); };
  
  const addPhone = () => { if (phones.length < 5) setPhones([...phones, ""]); };
  const removePhone = (index: number) => { const newP = phones.filter((_, i) => i !== index); setPhones(newP.length ? newP : [""]); };
  const handleSaveGeneral = async () => {
    setConfirmModal({ isOpen: true, title: "لطفاً صبر کنید...", type: 'warning', message: "در حال ذخیره اطلاعات...", showCancel: false, onConfirm: () => {} });
    try {
      await fetch("http://127.0.0.1:8000/api/settings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: "clinic_name", value: settings.clinic_name }) });
      await fetch("http://127.0.0.1:8000/api/settings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: "clinic_address", value: settings.clinic_address }) });
      await fetch("http://127.0.0.1:8000/api/settings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: "working_hours_text", value: settings.working_hours_text }) });
      await fetch("http://127.0.0.1:8000/api/settings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: "clinic_phone", value: JSON.stringify(phones.filter(p => p.trim())) }) });
      setConfirmModal({ isOpen: true, title: "موفقیت", type: 'success', message: "اطلاعات درمانگاه با موفقیت ذخیره شد.", showCancel: false, onConfirm: () => setConfirmModal(null) });
    } catch { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "مشکلی در ارتباط با سرور رخ داد.", showCancel: false, onConfirm: () => setConfirmModal(null) }); }
  };

  const handlePriceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = toEnglishDigits(e.target.value).replace(/\D/g, '');
    setNewServicePrice(raw ? parseInt(raw).toLocaleString('en-US') : ""); 
  };
  const handleToggleService = async (id: number, currentStatus: number) => { try { await fetch(`http://127.0.0.1:8000/api/services/${id}/toggle`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: currentStatus === 1 ? 0 : 1 }) }); fetchData(); } catch {} };
  const confirmDeleteService = (id: number, name: string) => { setConfirmModal({ isOpen: true, title: "حذف کامل خدمت", type: 'danger', showCancel: true, message: `آیا از حذف کامل خدمت «${name}» اطمینان دارید؟ این عمل قابل بازگشت نیست، اما تاریخچه نوبت‌های قبلی در سیستم حفظ خواهد شد.`, onConfirm: async () => { try { await fetch(`http://127.0.0.1:8000/api/services/${id}`, { method: "DELETE" }); fetchData(); setConfirmModal(null); } catch {} } }); };
  
  const startEditService = (s: Service) => { 
    setEditServiceId(s.id); 
    setNewServiceName(s.name); 
    setNewServicePrice(s.price ? s.price.toLocaleString('en-US') : ""); 
    setNewServiceGender(s.has_gender); 
  };
  
  const cancelEditService = () => { 
    setEditServiceId(null); 
    setNewServiceName(""); 
    setNewServicePrice(""); 
    setNewServiceGender(0); 
  };

  const handleSaveService = async (e: React.FormEvent) => {
    e.preventDefault(); if (!newServiceName.trim()) return;
    const price = parseInt(newServicePrice.replace(/\D/g, '')) || 0;
    if (services.some(s => s.name.trim() === newServiceName.trim() && s.id !== editServiceId)) { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "خدمتی با این نام از قبل وجود دارد.", showCancel: false, onConfirm: () => setConfirmModal(null) }); return; }
    try {
      let res;
      if (editServiceId) res = await fetch(`http://127.0.0.1:8000/api/services/${editServiceId}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: newServiceName, price, has_gender: newServiceGender }) });
      else res = await fetch("http://127.0.0.1:8000/api/services", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: newServiceName, price, has_gender: newServiceGender }) });
      if(!res.ok) { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "خطا در ثبت خدمت در سرور.", showCancel: false, onConfirm: () => setConfirmModal(null) }); return; }
      cancelEditService(); fetchData();
    } catch { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "خطا در ارتباط با سرور.", showCancel: false, onConfirm: () => setConfirmModal(null) }); }
  };

  const handleDragStart = (index: number) => { setDraggedServiceIndex(index); };
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedServiceIndex === null || draggedServiceIndex === index) return;
    const items = [...services];
    const draggedItem = items[draggedServiceIndex];
    items.splice(draggedServiceIndex, 1);
    items.splice(index, 0, draggedItem);
    setDraggedServiceIndex(index);
    setServices(items);
  };
  const handleDrop = async () => {
    setDraggedServiceIndex(null);
    const ordered_ids = services.map(s => s.id);
    try { await fetch("http://127.0.0.1:8000/api/services/reorder", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ordered_ids }) }); } catch {}
  };

  const toggleWorkingDay = (dayId: number) => { const isWorking = scheduleConfig.working_days.includes(dayId); setScheduleConfig({ ...scheduleConfig, working_days: isWorking ? scheduleConfig.working_days.filter(d => d !== dayId) : [...scheduleConfig.working_days, dayId] }); };
  const handleDaysAheadChange = (val: string) => { let num = parseInt(val.replace(/\D/g, ''), 10); if (isNaN(num)) num = 1; if (num > 60) num = 60; setScheduleConfig({...scheduleConfig, booking_days_ahead: num}); };
  const toggleBulkItem = (val: string) => { if (bulkSelected.includes(val)) setBulkSelected(bulkSelected.filter(v => v !== val)); else setBulkSelected([...bulkSelected, val]); };

  const handleServiceSelection = (val: string) => {
    setSelectedServiceId(val);
    if (val !== 'ALL') {
      const serviceObj = services.find(s => s.id.toString() === val);
      setSelectedGender(serviceObj?.has_gender === 1 ? "both" : "all");
    }
  };

  const addDefaultTime = () => {
    if (!selectedServiceId || newDefaultTime.includes("_")) return;
    setScheduleConfig(prev => {
      const newConfig = JSON.parse(JSON.stringify(prev));
      if (!newConfig.weekly_times) newConfig.weekly_times = {};

      if (selectedServiceId === 'ALL') {
        bulkSelected.forEach(val => {
          const [sId, g] = val.split('-');
          if (targetDay === 'all') {
            if (!newConfig.default_times[sId]) newConfig.default_times[sId] = {};
            if (!newConfig.default_times[sId][g]) newConfig.default_times[sId][g] = [];
            if (!newConfig.default_times[sId][g].includes(newDefaultTime)) newConfig.default_times[sId][g].push(newDefaultTime);
          } else {
            if (!newConfig.weekly_times[targetDay]) newConfig.weekly_times[targetDay] = {};
            if (!newConfig.weekly_times[targetDay][sId]) {
                newConfig.weekly_times[targetDay][sId] = newConfig.default_times[sId] ? JSON.parse(JSON.stringify(newConfig.default_times[sId])) : {};
            }
            if (!newConfig.weekly_times[targetDay][sId][g]) newConfig.weekly_times[targetDay][sId][g] = [];
            if (!newConfig.weekly_times[targetDay][sId][g].includes(newDefaultTime)) newConfig.weekly_times[targetDay][sId][g].push(newDefaultTime);
          }
        });
      } else {
        const sId = selectedServiceId;
        const isGendered = services.find(s => s.id.toString() === sId)?.has_gender === 1;
        let targets = ['all'];
        if (isGendered) targets = (selectedGender === 'both') ? ['male', 'female'] : [selectedGender];
        
        targets.forEach(g => {
          if (targetDay === 'all') {
            if (!newConfig.default_times[sId]) newConfig.default_times[sId] = {};
            if (!newConfig.default_times[sId][g]) newConfig.default_times[sId][g] = [];
            if (!newConfig.default_times[sId][g].includes(newDefaultTime)) newConfig.default_times[sId][g].push(newDefaultTime);
          } else {
            if (!newConfig.weekly_times[targetDay]) newConfig.weekly_times[targetDay] = {};
            if (!newConfig.weekly_times[targetDay][sId]) {
                newConfig.weekly_times[targetDay][sId] = newConfig.default_times[sId] ? JSON.parse(JSON.stringify(newConfig.default_times[sId])) : {};
            }
            if (!newConfig.weekly_times[targetDay][sId][g]) newConfig.weekly_times[targetDay][sId][g] = [];
            if (!newConfig.weekly_times[targetDay][sId][g].includes(newDefaultTime)) newConfig.weekly_times[targetDay][sId][g].push(newDefaultTime);
          }
        });
      }
      return newConfig;
    });
  };

  const removeDefaultTime = (sId: string, g: string, time: string) => {
    setScheduleConfig(prev => {
      const newConfig = JSON.parse(JSON.stringify(prev));
      if (targetDay === 'all') {
        if (newConfig.default_times[sId] && newConfig.default_times[sId][g]) {
          newConfig.default_times[sId][g] = newConfig.default_times[sId][g].filter((t: string) => t !== time);
        }
      } else {
        if (!newConfig.weekly_times[targetDay]) newConfig.weekly_times[targetDay] = {};
        if (!newConfig.weekly_times[targetDay][sId]) {
            newConfig.weekly_times[targetDay][sId] = newConfig.default_times[sId] ? JSON.parse(JSON.stringify(newConfig.default_times[sId])) : {};
        }
        if (newConfig.weekly_times[targetDay][sId][g]) {
          newConfig.weekly_times[targetDay][sId][g] = newConfig.weekly_times[targetDay][sId][g].filter((t: string) => t !== time);
        }
      }
      return newConfig;
    });
  };

  const clearAllDefaultTimes = (sId: string) => {
    setScheduleConfig(prev => {
      const newConfig = JSON.parse(JSON.stringify(prev));
      const isGendered = services.find(s => s.id.toString() === sId)?.has_gender === 1;
      let targets = ['all'];
      if (isGendered) targets = (selectedGender === 'both') ? ['male', 'female'] : [selectedGender];

      targets.forEach(g => {
        if (targetDay === 'all') {
          if (newConfig.default_times[sId] && newConfig.default_times[sId][g]) newConfig.default_times[sId][g] = [];
        } else {
          if (!newConfig.weekly_times[targetDay]) newConfig.weekly_times[targetDay] = {};
          if (!newConfig.weekly_times[targetDay][sId]) {
              newConfig.weekly_times[targetDay][sId] = newConfig.default_times[sId] ? JSON.parse(JSON.stringify(newConfig.default_times[sId])) : {};
          }
          newConfig.weekly_times[targetDay][sId][g] = [];
        }
      });
      return newConfig;
    });
  };

  const handleSaveScheduleConfig = async () => {
    setConfirmModal({ isOpen: true, title: "لطفاً صبر کنید...", type: 'warning', message: "در حال ساخت تقویم سیستم...", showCancel: false, onConfirm: () => {} });
    try {
      await fetch("http://127.0.0.1:8000/api/settings/schedule", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(scheduleConfig) });
      setConfirmModal({ isOpen: true, title: "موفقیت", type: 'success', message: "تقویم و ساعات کاری با موفقیت روی ربات اعمال شد.", showCancel: false, onConfirm: () => setConfirmModal(null) });
      fetchOverrideList();
    } catch { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "خطا در بروزرسانی تقویم.", showCancel: false, onConfirm: () => setConfirmModal(null) }); }
  };

  // Override Methods
  const getGregorianDateString = (dObj: DateObject) => new DateObject(dObj).convert(gregorian, gregorian_en).format("YYYY-MM-DD");
  const formatToJalali = (gregorianDateStr: string) => new DateObject({ date: gregorianDateStr, format: "YYYY-MM-DD", calendar: gregorian, locale: gregorian_en }).convert(persian, custom_fa).format("YYYY/MM/DD");

  const fetchOverrideSlots = useCallback(async () => {
    const dateStr = getGregorianDateString(overrideDateObj);
    if (!dateStr || !selectedServiceId || selectedServiceId === 'ALL') return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/schedule/slots?date=${dateStr}&service_id=${selectedServiceId}`);
      setOverrideSlots(await res.json());
    } catch {}
  }, [overrideDateObj, selectedServiceId]);

  useEffect(() => { const init = async () => { await fetchOverrideSlots(); }; init(); }, [fetchOverrideSlots]);

  const addOverrideTime = () => {
    if (!newOverrideTime.includes("_") && selectedServiceId !== 'ALL') {
      const isGendered = services.find(s => s.id.toString() === selectedServiceId)?.has_gender === 1;
      let targets = ['all'];
      if(isGendered) targets = (selectedGender === 'both') ? ['male', 'female'] : [selectedGender];
      
      setOverrideSlots(prev => {
        const newSlots = [...prev];
        targets.forEach(g => { if (!newSlots.find(s => s.time === newOverrideTime && s.gender === g)) newSlots.push({ time: newOverrideTime, gender: g }); });
        return newSlots;
      });
    }
  };

  const confirmSaveOverride = () => {
    const dateStr = getGregorianDateString(overrideDateObj);
    const dateFa = overrideDateObj.format("YYYY/MM/DD");
    if (!dateStr || !selectedServiceId || selectedServiceId === 'ALL') return;
    setConfirmModal({
      isOpen: true, title: "اعمال تغییرات روی تاریخ خاص", type: 'warning', showCancel: true,
      message: `شما در حال تغییر ساعات رزرو برای تاریخ ${dateFa} هستید. آیا مایل به ادامه هستید؟`,
      onConfirm: async () => {
        setConfirmModal({ isOpen: true, title: "لطفاً صبر کنید...", type: 'warning', message: "در حال ثبت اطلاعات...", showCancel: false, onConfirm: () => {} });
        try {
          await fetch("http://127.0.0.1:8000/api/schedule/override", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ date: dateStr, service_id: parseInt(selectedServiceId), slots: overrideSlots }) });
          setConfirmModal({ isOpen: true, title: "موفقیت", type: 'success', message: "تغییرات با موفقیت روی این روز اعمال شد.", showCancel: false, onConfirm: () => setConfirmModal(null) });
          fetchOverrideList();
        } catch { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "خطا در اعمال تغییرات.", showCancel: false, onConfirm: () => setConfirmModal(null) }); }
      }
    });
  };

  const resetOverride = (dateStr: string, sId: number) => {
    setConfirmModal({
      isOpen: true, title: "بازنشانی به تنظیمات پیش‌فرض", type: 'warning', showCancel: true,
      message: `آیا مایلید تغییرات اختصاصی این تاریخ پاک شود و دوباره از تنظیمات پیش‌فرض استفاده شود؟`,
      onConfirm: async () => {
        setConfirmModal({ isOpen: true, title: "لطفاً صبر کنید...", type: 'warning', message: "در حال بازنشانی...", showCancel: false, onConfirm: () => {} });
        try {
          await fetch(`http://127.0.0.1:8000/api/schedule/override?date=${dateStr}&service_id=${sId}`, { method: "DELETE" });
          if (getGregorianDateString(overrideDateObj) === dateStr && parseInt(selectedServiceId) === sId) fetchOverrideSlots();
          fetchOverrideList();
          setConfirmModal({ isOpen: true, title: "موفقیت", type: 'success', message: "این روز به تنظیمات پایه بازگشت.", showCancel: false, onConfirm: () => setConfirmModal(null) });
        } catch { setConfirmModal({ isOpen: true, title: "خطا", type: 'danger', message: "خطا در بازنشانی.", showCancel: false, onConfirm: () => setConfirmModal(null) }); }
      }
    });
  };

  const isSelectedServiceGendered = services.find(s => s.id.toString() === selectedServiceId)?.has_gender === 1;

  const servicesOptions = [
    { value: "ALL", label: "همه خدمات (عملیات دسته‌جمعی)" },
    ...services.map(s => ({ value: s.id.toString(), label: s.name }))
  ];

  const genderOptions = !isSelectedServiceGendered ? 
    [{ value: "all", label: "عمومی (بدون تفکیک)" }] :
    [
      { value: "both", label: "هر دو (آقا و خانم)" },
      { value: "male", label: "آقایان" },
      { value: "female", label: "بانوان" }
    ];

  const targetDayOptions = [
    { value: "all", label: "همه روزهای کاری (پیش‌فرض)" },
    ...weekDaysMap.map(d => ({ value: d.id.toString(), label: `فقط ${d.label}‌ها (اختصاصی)` }))
  ];

  const renderDefaultScheduleBoxes = () => {
    if (!selectedServiceId || selectedServiceId === 'ALL') {
      return <p className="text-gray-400 font-bold text-sm bg-white p-4 rounded-xl border border-gray-200 border-dashed text-center">یک خدمت انتخاب کنید تا ساعت‌های فعال آن نمایش داده شود.</p>;
    }
    
    let displayGenders = [];
    if (!isSelectedServiceGendered) displayGenders = ['all'];
    else {
      if (selectedGender === 'both') displayGenders = ['male', 'female'];
      else if (selectedGender === 'male') displayGenders = ['male'];
      else if (selectedGender === 'female') displayGenders = ['female'];
      else displayGenders = ['male', 'female'];
    }

    const elements = displayGenders.map(g => {
      let times = [];
      if (targetDay === 'all') times = scheduleConfig.default_times?.[selectedServiceId]?.[g] || [];
      else {
        const weekly = scheduleConfig.weekly_times?.[targetDay]?.[selectedServiceId]?.[g];
        if (weekly !== undefined) times = weekly;
        else times = scheduleConfig.default_times?.[selectedServiceId]?.[g] || [];
      }

      if (times.length === 0) return null;
      const genderLabel = g === "male" ? "مخصوص آقایان" : g === "female" ? "مخصوص بانوان" : "عمومی";
      return (
        <div key={g} className="flex flex-col sm:flex-row sm:items-center gap-4 p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
          <span className="font-bold text-sm text-gray-500 w-32 shrink-0">{genderLabel}:</span>
          <div className="flex flex-wrap gap-4 flex-1">
            {[...times].sort().map(t => (
              <div key={t} className="relative inline-flex items-center justify-center px-4 py-2.5 bg-slate-50 text-slate-800 rounded-xl font-mono text-lg font-bold border border-slate-200 shadow-sm group">
                {t}
                <button onClick={() => removeDefaultTime(selectedServiceId, g, t)} className="absolute -top-2 -right-2 bg-white text-red-500 hover:bg-red-500 hover:text-white border border-red-200 rounded-full p-1 shadow-sm transition-all opacity-0 group-hover:opacity-100 cursor-pointer"><X className="w-3.5 h-3.5"/></button>
              </div>
            ))}
          </div>
        </div>
      );
    });

    return elements.every(el => el === null) ? <p className="text-gray-400 font-bold text-sm bg-white p-4 rounded-xl border border-gray-200 border-dashed text-center">تایمی برای این حالت تنظیم نشده است.</p> : elements;
  };

  const renderOverrideScheduleBoxes = () => {
    if (!selectedServiceId || selectedServiceId === 'ALL') {
      return <p className="text-gray-400 font-bold text-sm bg-white p-4 rounded-xl border border-gray-200 border-dashed text-center">یک خدمت انتخاب کنید.</p>;
    }
    if (overrideSlots.length === 0) return <p className="text-gray-400 font-bold m-auto">هیچ نوبتی برای این روز تعریف نشده است (تعطیل).</p>;
    
    let displayGenders = [];
    if (!isSelectedServiceGendered) displayGenders = ['all'];
    else {
      if (selectedGender === 'both') displayGenders = ['male', 'female'];
      else if (selectedGender === 'male') displayGenders = ['male'];
      else if (selectedGender === 'female') displayGenders = ['female'];
      else displayGenders = ['male', 'female'];
    }

    const elements = displayGenders.map(g => {
      const times = overrideSlots.filter(s => s.gender === g);
      if (times.length === 0) return null;
      const genderLabel = g === "male" ? "مخصوص آقایان" : g === "female" ? "مخصوص بانوان" : "عمومی";
      return (
        <div key={g} className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 shadow-sm w-full">
          <span className="font-bold text-sm text-gray-500 w-32 shrink-0">{genderLabel}:</span>
          <div className="flex flex-wrap gap-4 flex-1">
            {[...times].sort((a,b)=>a.time.localeCompare(b.time)).map((slot, idx) => (
              <div key={idx} className="relative inline-flex flex-col items-center justify-center p-3 bg-white rounded-xl border border-gray-200 shadow-sm group">
                <span className="text-lg font-mono font-bold text-slate-800 leading-none">{slot.time}</span>
                <button onClick={() => setOverrideSlots(prev => prev.filter(s => !(s.time === slot.time && s.gender === g)))} className="absolute -top-2 -right-2 bg-white border border-red-200 text-red-500 hover:bg-red-500 hover:text-white rounded-full p-1 shadow-sm opacity-0 group-hover:opacity-100 transition-all cursor-pointer"><X className="w-3.5 h-3.5"/></button>
              </div>
            ))}
          </div>
        </div>
      );
    });

    return elements.every(el => el === null) ? <p className="text-gray-400 font-bold m-auto">هیچ نوبتی برای این حالت تعریف نشده است.</p> : elements;
  };

  const formatDetailedSlots = (slots: { time: string, gender: string }[], has_gender: number) => {
    if (slots.length === 0) return <span className="bg-red-50 text-red-600 px-3 py-1.5 rounded-lg text-xs font-bold w-full text-center block shadow-sm">کامل غیرفعال (تعطیل)</span>;
    if (has_gender === 0) {
      const times = [...slots].sort((a,b)=>a.time.localeCompare(b.time)).map(s => s.time);
      return <div className="text-sm font-medium text-gray-700 bg-white p-3 rounded-xl border border-gray-100 text-center"><span className="text-blue-600 font-bold ml-2">زمان‌ها:</span><span className="font-mono" dir="ltr">{times.join(" ، ")}</span></div>;
    }
    
    const males = [...slots].filter(s => s.gender === 'male').sort((a,b)=>a.time.localeCompare(b.time)).map(s => s.time);
    const females = [...slots].filter(s => s.gender === 'female').sort((a,b)=>a.time.localeCompare(b.time)).map(s => s.time);
    
    return (
      <div className="flex flex-col gap-2 w-full text-sm">
        <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100">
            <span className="font-bold text-gray-600">آقایان:</span>
            {males.length > 0 ? <span className="text-blue-600 font-mono font-bold" dir="ltr">{males.join(" ، ")}</span> : <span className="text-red-500 font-bold text-xs bg-red-50 px-2 py-1 rounded">تعطیل</span>}
        </div>
        <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-gray-100">
            <span className="font-bold text-gray-600">بانوان:</span>
            {females.length > 0 ? <span className="text-pink-600 font-mono font-bold" dir="ltr">{females.join(" ، ")}</span> : <span className="text-red-500 font-bold text-xs bg-red-50 px-2 py-1 rounded">تعطیل</span>}
        </div>
      </div>
    );
  };

  const getFilteredOverrides = () => {
    const query = toEnglishDigits(overrideSearchQuery.trim().toLowerCase());
    const listToFilter = overrideListMode === 'future' ? activeOverrides : historyLogs;
    return listToFilter.filter(item => {
      const theDate = formatToJalali(overrideListMode === 'future' ? (item as OverriddenDate).date : (item as HistoryLog).target_date);
      return theDate.includes(query) || item.service_name.toLowerCase().includes(query);
    });
  };

  const filteredOverrides = getFilteredOverrides();
  const totalOverridePages = Math.ceil(filteredOverrides.length / overrideRowsPerPage);
  const currentOverrideRows = filteredOverrides.slice((overrideCurrentPage - 1) * overrideRowsPerPage, overrideCurrentPage * overrideRowsPerPage);

  if (loading) return <div className="flex h-screen items-center justify-center"><div className="text-xl font-bold text-blue-600">بارگذاری تنظیمات...</div></div>;

  return (
    <div className="min-h-screen px-8 pt-12 pb-32 w-full relative bg-transparent">
      <header className="flex items-center justify-between mb-8 border-b-transparent">
        <h1 className="text-3xl font-bold text-gray-800 leading-none">تنظیمات سیستم</h1>
      </header>

      <div className="flex gap-2 border-b border-gray-200 mb-8 overflow-x-auto">
        <button onClick={() => setActiveTab('general')} className={`px-6 py-4 font-bold text-sm flex items-center gap-2 border-b-2 cursor-pointer transition-colors whitespace-nowrap ${activeTab === 'general' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-t-xl'}`}><Store className="w-5 h-5"/> اطلاعات درمانگاه</button>
        <button onClick={() => setActiveTab('services')} className={`px-6 py-4 font-bold text-sm flex items-center gap-2 border-b-2 cursor-pointer transition-colors whitespace-nowrap ${activeTab === 'services' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-t-xl'}`}><Stethoscope className="w-5 h-5"/> مدیریت خدمات</button>
        <button onClick={() => setActiveTab('schedule')} className={`px-6 py-4 font-bold text-sm flex items-center gap-2 border-b-2 cursor-pointer transition-colors whitespace-nowrap ${activeTab === 'schedule' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-t-xl'}`}><Clock className="w-5 h-5"/> تقویم و ساعات کاری</button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 w-full mb-8">
        
        {activeTab === 'general' && (
          <div className="space-y-8 animate-fade-in max-w-3xl">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">نام درمانگاه:</label>
              <div className="flex items-center w-full border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-500 bg-white shadow-sm transition-all overflow-hidden h-12">
                <input type="text" name="clinic_name" value={settings.clinic_name} onChange={handleSettingChange} maxLength={50} className="flex-1 px-4 h-full outline-none bg-transparent" />
                <div className="h-full bg-gray-50 border-r border-gray-100 px-3 flex items-center justify-center">
                   <span className="text-xs font-bold text-gray-400 font-mono" dir="ltr">{settings.clinic_name.length}/50</span>
                </div>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">شماره‌های تماس (نمایش در ربات - حداکثر ۵ عدد):</label>
              <div className="space-y-3">
                {phones.map((phone, index) => (
                  <div key={index} className="flex gap-3">
                    <div className="flex-1 flex items-center border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-500 bg-white shadow-sm transition-all overflow-hidden h-12" dir="ltr">
                      <input type="text" value={phone} onChange={e => handlePhoneChange(index, e.target.value)} maxLength={11} className="flex-1 px-4 h-full outline-none font-mono tracking-widest text-left bg-transparent placeholder:text-gray-300" placeholder="0912..." />
                      <div className="h-full bg-gray-50 border-l border-gray-100 px-3 flex items-center justify-center">
                         <span className="text-xs font-bold text-gray-400 font-mono" dir="ltr">{phone.length}/11</span>
                      </div>
                    </div>
                    <button onClick={() => removePhone(index)} className="w-12 h-12 shrink-0 flex items-center justify-center bg-red-50 text-red-500 rounded-xl hover:bg-red-100 transition-colors cursor-pointer"><Trash2 className="w-5 h-5"/></button>
                  </div>
                ))}
                {phones.length < 5 && (
                  <div className="flex gap-3 mt-3">
                    <div className="flex-1"></div>
                    <button onClick={addPhone} className="w-12 h-12 shrink-0 flex items-center justify-center bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition-colors cursor-pointer"><Plus className="w-5 h-5"/></button>
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">توضیحات زمان کاری:</label>
              <div className="flex flex-col w-full border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-500 bg-white shadow-sm overflow-hidden transition-all">
                <textarea name="working_hours_text" value={settings.working_hours_text} onChange={handleSettingChange} maxLength={100} rows={2} placeholder="مثال: همه‌روزه به جز جمعه‌ها" className="w-full px-4 py-3 outline-none resize-none bg-transparent" />
                <div className="bg-gray-50 border-t border-gray-100 px-4 py-1.5 flex justify-end items-center">
                   <span className="text-xs font-bold text-gray-400 font-mono" dir="ltr">{settings.working_hours_text.length}/100</span>
                </div>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">آدرس دقیق درمانگاه:</label>
              <div className="flex flex-col w-full border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-blue-500 bg-white shadow-sm overflow-hidden transition-all">
                <textarea name="clinic_address" value={settings.clinic_address} onChange={handleSettingChange} rows={3} maxLength={250} className="w-full px-4 py-3 outline-none resize-none bg-transparent" />
                <div className="bg-gray-50 border-t border-gray-100 px-4 py-1.5 flex justify-end items-center">
                   <span className="text-xs font-bold text-gray-400 font-mono" dir="ltr">{settings.clinic_address.length}/250</span>
                </div>
              </div>
            </div>
            
            <div className="pt-4 border-t border-gray-100"><button onClick={handleSaveGeneral} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 h-12 rounded-xl font-bold shadow-sm cursor-pointer"><Save className="w-5 h-5" /> ذخیره اطلاعات</button></div>
          </div>
        )}

        {activeTab === 'services' && (
          <div className="animate-fade-in w-full">
            <form onSubmit={handleSaveService} className="flex flex-col md:flex-row gap-4 mb-8 p-6 bg-gray-50 rounded-2xl border border-gray-100 shadow-sm items-end">
              <div className="flex-1 w-full">
                <label className="block text-xs font-bold text-gray-500 mb-1">نام خدمت:</label>
                <input type="text" value={newServiceName} onChange={e => setNewServiceName(e.target.value)} maxLength={50} placeholder="مثال: فصد..." className="w-full px-4 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none bg-white shadow-sm" required />
              </div>
              <div className="w-full md:w-48">
                <label className="block text-xs font-bold text-gray-500 mb-1">هزینه (تومان):</label>
                <input type="text" value={newServicePrice} onChange={handlePriceChange} placeholder="رایگان = 0" className="w-full px-4 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none bg-white font-mono font-bold text-right placeholder:text-sm placeholder-gray-400 shadow-sm" dir="rtl" />
              </div>
              <div className="w-full md:w-48">
                <label className="block text-xs font-bold text-gray-500 mb-1">نوع خدمت:</label>
                <select value={newServiceGender} onChange={e => setNewServiceGender(parseInt(e.target.value))} className="w-full px-4 h-12 border border-gray-200 rounded-xl outline-none bg-white cursor-pointer font-bold text-sm shadow-sm">
                  <option value={0}>عمومی</option>
                  <option value={1}>تفکیک جنسیت دارد</option>
                </select>
              </div>
              <div className="flex gap-2 w-full md:w-auto">
                {editServiceId && <button type="button" onClick={cancelEditService} className="flex items-center justify-center bg-gray-200 hover:bg-gray-300 text-gray-700 w-12 h-12 rounded-xl transition-colors cursor-pointer"><X className="w-5 h-5"/></button>}
                <button type="submit" className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white px-8 h-12 rounded-xl font-bold shadow-sm cursor-pointer">{editServiceId ? <Save className="w-5 h-5"/> : <Plus className="w-5 h-5"/>} {editServiceId ? "ذخیره تغییرات" : "افزودن خدمت"}</button>
              </div>
            </form>
            
            <div className="space-y-3">
              <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2"><Stethoscope className="w-5 h-5 text-blue-600" /> مدیریت خدمات سیستم</h3>
              <p className="text-xs font-bold text-gray-500 mb-4 bg-blue-50 p-3 rounded-lg border border-blue-100 flex items-center gap-2"><AlertCircle className="w-4 h-4 text-blue-600"/> با کشیدن و رها کردن آیکون ☰ می‌توانید ترتیب نمایش خدمات در ربات بله را تغییر دهید.</p>
              <div className="overflow-x-auto rounded-xl border border-gray-100">
                <table className="w-full text-right">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr><th className="p-4 w-12"></th><th className="p-4 font-bold text-gray-600 text-sm">نام خدمت</th><th className="p-4 font-bold text-gray-600 text-sm text-center">هزینه (تومان)</th><th className="p-4 font-bold text-gray-600 text-sm text-center">تفکیک جنسیتی</th><th className="p-4 font-bold text-gray-600 text-sm text-center">وضعیت در ربات</th><th className="p-4 font-bold text-gray-600 text-sm text-center">عملیات</th></tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {services.map((s, index) => (
                      <tr 
                        key={s.id} 
                        draggable 
                        onDragStart={() => handleDragStart(index)}
                        onDragOver={(e) => handleDragOver(e, index)}
                        onDragEnd={handleDrop}
                        className={`transition-colors ${draggedServiceIndex === index ? 'bg-blue-50 opacity-50' : 'hover:bg-gray-50 bg-white'}`}
                      >
                        <td className="p-4 cursor-grab active:cursor-grabbing text-gray-400 hover:text-blue-600 transition-colors" title="بکشید و رها کنید"><GripVertical className="w-5 h-5"/></td>
                        <td className={`p-4 font-bold ${s.is_active === 1 ? 'text-gray-800' : 'text-gray-400'}`}>{s.name}</td>
                        <td className="p-4 text-center">
                          {s.price > 0 ? <span className="font-mono text-gray-700 font-bold">{s.price.toLocaleString('en-US')}</span> : <span className="bg-emerald-50 text-emerald-600 px-3 py-1 rounded font-bold text-xs">رایگان</span>}
                        </td>
                        <td className="p-4 text-center"><span className={`px-3 py-1.5 text-xs font-bold rounded-lg border ${s.has_gender === 1 ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-red-50 text-red-600 border-red-100'}`}>{s.has_gender === 1 ? 'دارد' : 'ندارد'}</span></td>
                        <td className="p-4 text-center"><span className={`px-3 py-1.5 text-xs font-bold rounded-lg ${s.is_active === 1 ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-100 text-slate-500'}`}>{s.is_active === 1 ? 'فعال' : 'غیرفعال (مخفی)'}</span></td>
                        <td className="p-4 flex justify-center gap-2">
                          <button onClick={() => handleToggleService(s.id, s.is_active)} title={s.is_active === 1 ? 'غیرفعال کردن' : 'فعال کردن'} className="p-2 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg cursor-pointer"><CheckCircle className="w-4 h-4"/></button>
                          <button onClick={() => startEditService(s)} title="ویرایش" className="p-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg cursor-pointer"><Edit className="w-4 h-4"/></button>
                          <button onClick={() => confirmDeleteService(s.id, s.name)} title="حذف کامل" className="p-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg cursor-pointer"><Trash2 className="w-4 h-4"/></button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'schedule' && (
          <div className="animate-fade-in w-full pb-20">
            <div className="flex gap-2 mb-6 border-b border-gray-100 pb-4">
              <button onClick={() => setScheduleSubTab('defaults')} className={`px-4 py-2 font-bold rounded-xl text-sm transition-all cursor-pointer ${scheduleSubTab === 'defaults' ? 'bg-blue-100 text-blue-700' : 'bg-transparent text-gray-500 hover:bg-gray-50'}`}>تنظیمات پایه و پیش‌فرض</button>
              <button onClick={() => setScheduleSubTab('overrides')} className={`px-4 py-2 font-bold rounded-xl text-sm transition-all cursor-pointer ${scheduleSubTab === 'overrides' ? 'bg-amber-100 text-amber-700' : 'bg-transparent text-gray-500 hover:bg-gray-50'}`}>تغییرات برای یک روز خاص</button>
            </div>

            {scheduleSubTab === 'defaults' && (
              <div className="space-y-10 max-w-4xl">
                <div>
                  <label className="block text-sm font-bold text-gray-800 mb-3">روزهای کاری مطب (فعال در ربات):</label>
                  <div className="flex flex-wrap gap-3">
                    {weekDaysMap.map(day => {
                      const isActive = scheduleConfig.working_days.includes(day.id);
                      return (
                        <button key={day.id} onClick={() => toggleWorkingDay(day.id)} className={`px-6 py-3 rounded-xl text-sm font-bold transition-all cursor-pointer shadow-sm ${isActive ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-white text-gray-400 border border-gray-200 hover:bg-gray-50'}`}>
                          {day.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold text-gray-800 mb-3">افق دید روزهای تقویم:</label>
                  <div className="flex items-center gap-3 bg-gray-50 p-4 rounded-2xl border border-gray-100 w-max">
                    <span className="text-gray-600 font-bold text-sm">بازه زمانی نمایش نوبت‌ها در ربات، برابر است با</span>
                    <input type="number" value={scheduleConfig.booking_days_ahead.toString()} onChange={e => handleDaysAheadChange(e.target.value)} className="w-20 px-3 h-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-center font-bold text-xl bg-white shadow-sm" min="1" max="60" />
                    <span className="text-gray-600 font-bold text-sm">روزِ کاریِ آینده.</span>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-8">
                  <h3 className="font-bold text-xl text-gray-800 mb-4 flex items-center gap-2"><Clock className="w-6 h-6 text-blue-600"/> برنامه‌ریزی ساعات پیش‌فرض برای هر خدمت</h3>
                  
                  <div className="mb-6 bg-blue-50 border border-blue-100 p-4 rounded-xl flex items-center gap-4">
                    <label className="text-sm font-bold text-blue-800 shrink-0">اعمال این تنظیمات روی:</label>
                    <div className="w-64">
                       <CustomSelect value={targetDay} onChange={setTargetDay} options={targetDayOptions} />
                    </div>
                  </div>

                  <div className="bg-gray-50 p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-gray-500 mb-2">انتخاب خدمت:</label>
                        <CustomSelect value={selectedServiceId} onChange={handleServiceSelection} options={servicesOptions} grid={true} />
                      </div>
                      
                      {selectedServiceId !== 'ALL' ? (
                        <>
                          <div>
                            <label className="block text-xs font-bold text-gray-500 mb-2">تفکیک جنسیت:</label>
                            <CustomSelect value={selectedGender} onChange={setSelectedGender} options={genderOptions} disabled={!isSelectedServiceGendered} />
                          </div>
                          <div>
                            <label className="block text-xs font-bold text-gray-500 mb-2">اضافه کردن ساعت:</label>
                            <div className="flex gap-2">
                              <TimeInput value={newDefaultTime} onChange={setNewDefaultTime} onEnter={addDefaultTime} />
                              <button onClick={addDefaultTime} disabled={!selectedServiceId} className="flex-1 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 shadow-sm cursor-pointer">افزودن</button>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="col-span-2">
                            <label className="block text-xs font-bold text-gray-500 mb-2">اضافه کردن ساعت به <span className="text-blue-600 text-sm">تمامی موارد تیک‌خورده</span> در پایین:</label>
                            <div className="flex gap-2 max-w-sm">
                              <TimeInput value={newDefaultTime} onChange={setNewDefaultTime} onEnter={addDefaultTime} />
                              <button onClick={addDefaultTime} className="flex-1 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-sm cursor-pointer">اعمال دسته‌جمعی</button>
                            </div>
                        </div>
                      )}
                    </div>

                    {selectedServiceId === 'ALL' && (
                      <div className="pt-4 border-t border-gray-200 animate-fade-in">
                        <p className="text-sm font-bold text-gray-700 mb-3">انتخاب سرویس‌هایی که ساعت بالا به آن‌ها اضافه شود:</p>
                        <div className="flex flex-wrap gap-2">
                          {services.flatMap(s => s.has_gender === 1 ? [{id: s.id.toString(), g: 'male', label: s.name + ' (آقایان)'}, {id: s.id.toString(), g: 'female', label: s.name + ' (بانوان)'}] : [{id: s.id.toString(), g: 'all', label: s.name + ' (عمومی)'}]).map(sg => {
                            const key = `${sg.id}-${sg.g}`;
                            const isChecked = bulkSelected.includes(key);
                            return (
                              <label key={key} className={`flex items-center gap-2 cursor-pointer px-3 py-2 rounded-lg border transition-all ${isChecked ? 'bg-blue-50 border-blue-200 shadow-sm' : 'bg-white border-gray-200 opacity-60'}`}>
                                <input type="checkbox" checked={isChecked} onChange={() => toggleBulkItem(key)} className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                                <span className={`text-sm font-bold ${isChecked ? 'text-blue-800' : 'text-gray-500'}`}>{sg.label}</span>
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    <div className="pt-6 border-t border-gray-200">
                      <div className="flex justify-between items-center mb-4">
                        <p className="text-sm font-bold text-gray-700">ساعت‌های فعال :</p>
                        {selectedServiceId && selectedServiceId !== 'ALL' && (
                          <button onClick={() => clearAllDefaultTimes(selectedServiceId)} className="text-xs bg-red-50 text-red-600 font-bold px-3 py-1.5 rounded-lg hover:bg-red-100 transition-colors cursor-pointer flex items-center gap-1"><Trash2 className="w-3.5 h-3.5"/> پاک کردن همه (تعطیل)</button>
                        )}
                      </div>
                      <div className="space-y-4">
                        {renderDefaultScheduleBoxes()}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-6 flex items-center justify-between border-t border-gray-100 bg-white p-4 rounded-2xl shadow-sm border">
                  <p className="text-xs text-gray-500 font-bold max-w-sm">⚠️ تغییرات این صفحه فقط زمانی روی ربات اعمال می‌شود که تقویم را ذخیره کنید.</p>
                  <div className="flex gap-3">
                    <button onClick={fetchData} className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 h-12 rounded-xl font-bold shadow-sm cursor-pointer"><RotateCcw className="w-5 h-5"/> لغو تغییرات من</button>
                    <button onClick={handleSaveScheduleConfig} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 h-12 rounded-xl font-bold shadow-md cursor-pointer"><Save className="w-5 h-5" /> ذخیره تقویم سیستم</button>
                  </div>
                </div>
              </div>
            )}

            {scheduleSubTab === 'overrides' && (
              <div className="space-y-8 max-w-full">
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-6 flex items-start gap-3 max-w-4xl">
                  <AlertCircle className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-sm font-bold text-amber-800 leading-relaxed">
                    با تغییر در این صفحه می‌توانید برای یک روزِ خاص، ساعت‌های متفاوتی تعریف کنید یا کل نوبت‌های آن روز را پاک کنید.<br/>
                    <span className="text-red-600">اخطار:</span> حذف یک ساعتی که بیمار قبلاً در آن رزرو کرده باشد، نوبت وی را لغو می‌کند و ربات برایش پیام ارسال می‌نماید.
                  </p>
                </div>
                
                <div className="bg-white border border-gray-200 rounded-2xl p-6 flex flex-col md:flex-row gap-6 items-end shadow-sm max-w-4xl">
                  <div className="flex-1 w-full relative">
                    <label className="flex items-center gap-2 text-sm font-bold text-gray-700 mb-2"><CalendarDays className="w-4 h-4"/> انتخاب تاریخ مورد نظر:</label>
                    <DatePicker calendar={persian} locale={custom_fa} value={overrideDateObj} onChange={(dateObject: DateObject | null) => { if (dateObject) setOverrideDateObj(dateObject); }} containerClassName="w-full" inputClass="w-full px-4 h-12 border border-gray-200 rounded-xl outline-none font-bold text-center bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white transition-colors cursor-pointer" editable={false} />
                  </div>
                  <div className="flex-1 w-full">
                    <label className="block text-sm font-bold text-gray-700 mb-2">انتخاب خدمت:</label>
                    <CustomSelect value={selectedServiceId === 'ALL' ? '' : selectedServiceId} onChange={handleServiceSelection} options={servicesOptions.filter(o => o.value !== 'ALL')} grid={true} />
                  </div>
                </div>

                {overrideDateObj && selectedServiceId && selectedServiceId !== 'ALL' && (
                  <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm animate-fade-in max-w-4xl">
                    <div className="flex justify-between items-center mb-6 border-b border-gray-100 pb-4">
                      <h3 className="font-bold text-lg text-gray-800">ساعات فعال در این تاریخ</h3>
                      <div className="flex gap-2 items-center">
                        <div className="w-48">
                           <CustomSelect value={selectedGender} onChange={setSelectedGender} disabled={!isSelectedServiceGendered} options={genderOptions} />
                        </div>
                        <TimeInput value={newOverrideTime} onChange={setNewOverrideTime} onEnter={addOverrideTime} />
                        <button onClick={addOverrideTime} className="bg-blue-600 text-white px-6 h-12 rounded-xl font-bold hover:bg-blue-700 shadow-sm cursor-pointer">اضافه</button>
                      </div>
                    </div>
                    
                    <div className="flex flex-col gap-4 p-6 bg-gray-50 rounded-xl border border-gray-100 min-h-24">
                      {renderOverrideScheduleBoxes()}
                    </div>
                    
                    <div className="mt-6 flex justify-between items-center">
                      <button onClick={() => setOverrideSlots([])} className="flex items-center gap-1.5 px-4 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-xl text-sm font-bold transition-colors cursor-pointer"><Trash2 className="w-4 h-4"/> پاک کردن همه (تعطیل موقت)</button>
                      <button onClick={confirmSaveOverride} className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-8 h-12 rounded-xl font-bold shadow-md cursor-pointer"><AlertCircle className="w-5 h-5"/> ثبت نهایی و اعمال تغییرات این روز</button>
                    </div>
                  </div>
                )}

                {/* Overrides History / List Section (Table UI) */}
                <div className="mt-12 pt-8 border-t border-gray-200">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                    <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2"><History className="w-6 h-6 text-blue-600" /> مدیریت استثنائات اختصاصی تقویم</h3>
                    
                    <div className="flex items-center gap-4">
                      <div className="relative w-64 h-11 hidden md:block">
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none"><Search className="h-4 w-4 text-gray-400" /></div>
                        <input type="text" placeholder="جستجو (تاریخ، خدمت)..." className="block w-full h-full pr-9 pl-3 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none shadow-sm" value={overrideSearchQuery} onChange={(e) => { setOverrideSearchQuery(e.target.value); setOverrideCurrentPage(1); }} />
                      </div>
                      
                      <div className="flex bg-gray-100 p-1 rounded-xl shrink-0">
                        <button onClick={() => { setOverrideListMode('future'); setOverrideCurrentPage(1); }} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer ${overrideListMode === 'future' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>لیست پیش‌رو</button>
                        <button onClick={() => { setOverrideListMode('history'); setOverrideCurrentPage(1); }} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer ${overrideListMode === 'history' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>تاریخچه گذشته</button>
                      </div>
                    </div>
                  </div>
                  
                  {filteredOverrides.length === 0 ? (
                     <div className="text-center py-12 bg-white rounded-2xl border border-gray-100 border-dashed">
                       <p className="text-gray-500 font-bold">موردی برای نمایش یافت نشد.</p>
                     </div>
                  ) : (
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col mb-4 animate-fade-in">
                      <div className="overflow-x-auto">
                        <table className="w-full text-right">
                          <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                              <th className="p-4 text-gray-600 font-bold text-sm w-16">ردیف</th>
                              <th className="p-4 text-gray-600 font-bold text-sm w-36">تاریخ {overrideListMode === 'history' ? 'مقرر' : 'تغییر'}</th>
                              <th className="p-4 text-gray-600 font-bold text-sm w-48">نام خدمت</th>
                              <th className="p-4 text-gray-600 font-bold text-sm min-w-80">وضعیت زمان‌های اختصاصی (ساعات رزرو)</th>
                              {overrideListMode === 'history' ? (
                                <th className="p-4 text-gray-600 font-bold text-sm">شرح وضعیت و توضیحات لاگ</th>
                              ) : (
                                <th className="p-4 text-gray-600 font-bold text-sm text-center w-36">عملیات</th>
                              )}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {currentOverrideRows.map((item, idx) => {
                              const rowNumber = (overrideCurrentPage - 1) * overrideRowsPerPage + idx + 1;
                              const theDate = formatToJalali(overrideListMode === 'future' ? (item as OverriddenDate).date : (item as HistoryLog).target_date);
                              
                              return (
                                <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                  <td className="p-4 text-gray-500 font-bold text-sm">{rowNumber}</td>
                                  <td className="p-4 text-gray-800 font-bold">{theDate}</td>
                                  <td className="p-4 text-blue-700 font-bold text-sm">{item.service_name}</td>
                                  <td className="p-4">
                                     {formatDetailedSlots(item.slots, (item as OverriddenDate).has_gender ?? 1)}
                                  </td>
                                  {overrideListMode === 'history' ? (
                                    <td className="p-4">
                                      <p className="text-xs font-bold text-gray-600 bg-gray-100 p-2.5 rounded-lg border border-gray-200 leading-relaxed max-w-sm">{(item as HistoryLog).status_msg}</p>
                                    </td>
                                  ) : (
                                    <td className="p-4 flex justify-center items-center mt-2">
                                       <button onClick={() => resetOverride((item as OverriddenDate).date, (item as OverriddenDate).service_id)} className="flex items-center gap-1 bg-red-50 hover:bg-red-100 text-red-600 px-3 py-2 rounded-xl text-xs font-bold transition-colors cursor-pointer shadow-sm"><Trash2 className="w-3.5 h-3.5"/> بازنشانی</button>
                                    </td>
                                  )}
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Pagination for Overrides Table */}
                  {filteredOverrides.length > 0 && (
                    <div className="flex flex-col sm:flex-row justify-between items-center p-4 bg-white border border-gray-200 rounded-xl shadow-sm gap-4">
                      <div className="flex items-center gap-2 text-sm font-bold text-gray-600">
                        <span>نمایش</span>
                        <select value={overrideRowsPerPage} onChange={(e) => { setOverrideRowsPerPage(Number(e.target.value)); setOverrideCurrentPage(1); }} className="border border-gray-200 rounded-lg px-2 py-1 outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50 cursor-pointer">
                          {[5, 10, 20, 50].map(n => <option key={n} value={n}>{n}</option>)}
                        </select>
                        <span>ردیف</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => setOverrideCurrentPage(prev => Math.max(prev - 1, 1))} disabled={overrideCurrentPage === 1} className="w-8 h-8 flex items-center justify-center rounded-lg bg-gray-50 border border-gray-200 text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors cursor-pointer"><ChevronRight className="w-4 h-4" /></button>
                        <div className="flex gap-1">
                          {getPageNumbers(overrideCurrentPage, totalOverridePages).map((pageNum, idx) => (
                            pageNum === "..." ? <span key={idx} className="w-8 h-8 flex items-center justify-center text-gray-400 font-bold text-xs">...</span> :
                            <button key={idx} onClick={() => setOverrideCurrentPage(pageNum as number)} className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-bold transition-all cursor-pointer ${overrideCurrentPage === pageNum ? 'bg-blue-600 text-white shadow-md' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}`}>{pageNum}</button>
                          ))}
                        </div>
                        <button onClick={() => setOverrideCurrentPage(prev => Math.min(prev + 1, totalOverridePages))} disabled={overrideCurrentPage === totalOverridePages || totalOverridePages === 0} className="w-8 h-8 flex items-center justify-center rounded-lg bg-gray-50 border border-gray-200 text-gray-600 disabled:opacity-50 hover:bg-gray-100 transition-colors cursor-pointer"><ChevronLeft className="w-4 h-4" /></button>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-white w-full max-w-md rounded-3xl shadow-2xl overflow-hidden border border-gray-100">
            <div className="p-8">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 ${confirmModal.type === 'danger' ? 'bg-red-50' : confirmModal.type === 'success' ? 'bg-green-50' : 'bg-amber-50'}`}>
                {confirmModal.type === 'success' ? <CheckCircle className="w-10 h-10 text-green-500" /> : <AlertCircle className={`w-10 h-10 ${confirmModal.type === 'danger' ? 'text-red-500' : 'text-amber-500'}`} />}
              </div>
              <h3 className="text-2xl font-bold text-center text-gray-800 mb-4">{confirmModal.title}</h3>
              <p className="text-center text-gray-600 mb-8 leading-relaxed font-medium">{confirmModal.message}</p>
              <div className="flex gap-4">
                {confirmModal.showCancel && <button onClick={() => setConfirmModal(null)} className="flex-1 py-3.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-colors cursor-pointer">انصراف</button>}
                <button onClick={confirmModal.onConfirm} className={`flex-1 py-3.5 text-white rounded-xl font-bold transition-colors shadow-lg cursor-pointer ${confirmModal.type === 'danger' ? 'bg-red-500 hover:bg-red-600 shadow-red-200' : confirmModal.type === 'success' ? 'bg-green-500 hover:bg-green-600 shadow-green-200' : 'bg-amber-500 hover:bg-amber-600 shadow-amber-200'}`}>تایید</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}