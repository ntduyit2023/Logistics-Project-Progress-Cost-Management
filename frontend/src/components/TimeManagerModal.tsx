import React, { useState, useEffect } from 'react';
import { X, Calendar, Plus, Save, Clock } from 'lucide-react';
import { api } from '../services/api';

interface TimeManagerModalProps {
  isOpen: boolean;
  onClose: (refresh?: boolean) => void;
  projectId: number | string;
  initialTimeConstraint: any;
  projectData?: any;
}

const DEFAULT_SCHEDULE = {
  monday: [],
  tuesday: [],
  wednesday: [],
  thursday: [],
  friday: [],
  saturday: [],
  sunday: []
};

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

const normalizeWeeklySchedule = (rawSchedule: any) => {
  if (!rawSchedule || typeof rawSchedule !== 'object') return DEFAULT_SCHEDULE;
  const result: Record<string, string[]> = {
    monday: [],
    tuesday: [],
    wednesday: [],
    thursday: [],
    friday: [],
    saturday: [],
    sunday: []
  };

  DAYS.forEach(day => {
    const titleKey = day.charAt(0).toUpperCase() + day.slice(1);
    const dayData = rawSchedule[day] !== undefined ? rawSchedule[day] : rawSchedule[titleKey];

    if (!dayData) return;

    if (Array.isArray(dayData)) {
      result[day] = dayData.map((item: any) => {
        if (typeof item === 'string') return item;
        if (item && item.start_time && item.end_time) return `${item.start_time}-${item.end_time}`;
        return String(item);
      });
    } else if (typeof dayData === 'object') {
      const shifts = dayData.shifts || [];
      if (Array.isArray(shifts)) {
        result[day] = shifts.map((s: any) => {
          if (typeof s === 'string') return s;
          const start = s.start_time || s.start || '08:00';
          const end = s.end_time || s.end || '12:00';
          return `${start}-${end}`;
        });
      }
    }
  });

  return result;
};

const TimeInput = ({ value, onChange }: { value: string, onChange: (v: string) => void }) => {
  const parts = value ? value.split(':') : ["08", "00"];
  const [hour, setHour] = useState(parts[0] || "08");
  const [minute, setMinute] = useState(parts[1] || "00");

  useEffect(() => {
    const p = value ? value.split(':') : ["08", "00"];
    setHour(p[0]);
    setMinute(p[1]);
  }, [value]);

  const handleBlur = () => {
    let h = parseInt(hour || "0");
    let m = parseInt(minute || "0");
    if (isNaN(h)) h = 0;
    if (isNaN(m)) m = 0;
    if (h > 23) h = 23;
    if (m > 59) m = 59;
    const finalH = h.toString().padStart(2, '0');
    const finalM = m.toString().padStart(2, '0');
    setHour(finalH);
    setMinute(finalM);
    onChange(`${finalH}:${finalM}`);
  };

  return (
    <div className="flex items-center w-full min-w-0 border border-slate-300 rounded-md bg-white focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 overflow-hidden">
      <input
        type="text"
        value={hour}
        onChange={e => setHour(e.target.value.replace(/\D/g, '').slice(0, 2))}
        onBlur={handleBlur}
        className="w-full text-center px-0.5 py-1.5 text-xs focus:outline-none bg-transparent"
      />
      <span className="text-slate-400 font-bold pb-0.5">:</span>
      <input
        type="text"
        value={minute}
        onChange={e => setMinute(e.target.value.replace(/\D/g, '').slice(0, 2))}
        onBlur={handleBlur}
        className="w-full text-center px-0.5 py-1.5 text-xs focus:outline-none bg-transparent"
      />
    </div>
  );
};

const DayScheduleRow = ({ day, intervals, onAdd, onRemove }: any) => {
  const [start, setStart] = useState("08:00");
  const [end, setEnd] = useState("12:00");

  return (
    <div className="flex flex-col p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all">
      <div className="font-bold text-slate-800 capitalize mb-3 pb-2 border-b border-slate-100 flex items-center justify-between">
        {day}
        {Array.isArray(intervals) && intervals.length > 0 ? (
          <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full font-medium">{intervals.length} shifts</span>
        ) : (
          <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full font-medium">Off</span>
        )}
      </div>

      <div className="flex flex-col gap-3 flex-1">
        {/* List of existing intervals */}
        <div className="flex flex-col gap-2">
          {Array.isArray(intervals) && intervals.map((interval: string, idx: number) => (
            <div key={idx} className="bg-indigo-50/50 border border-indigo-100/80 px-3 py-1.5 rounded-lg text-sm font-medium text-indigo-700 flex items-center justify-between shadow-sm">
              <div className="flex items-center">
                <Clock size={14} className="mr-2 text-indigo-400" />
                {interval}
              </div>
              <button onClick={() => onRemove(idx)} className="text-indigo-300 hover:text-red-500 hover:bg-red-50 p-1 rounded transition focus:outline-none">
                <X size={14} strokeWidth={2.5} />
              </button>
            </div>
          ))}
          {(!Array.isArray(intervals) || intervals.length === 0) && (
            <div className="flex items-center justify-center py-4 bg-slate-50/50 rounded-lg border border-slate-100 border-dashed">
              <span className="text-sm text-slate-400 italic">No shifts configured</span>
            </div>
          )}
        </div>

        {/* Add custom interval inline */}
        <div className="mt-auto pt-3 border-t border-slate-100">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-1 w-full">
              <TimeInput value={start} onChange={setStart} />
              <span className="text-slate-400 text-xs font-medium">-</span>
              <TimeInput value={end} onChange={setEnd} />
            </div>
            <button
              onClick={() => { onAdd(start, end); }}
              className="w-full shrink-0 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-md text-xs font-bold transition-colors shadow-sm flex items-center justify-center"
            >
              <Plus size={14} className="mr-1" /> Add Shift
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const TimeManagerModal: React.FC<TimeManagerModalProps> = ({ isOpen, onClose, projectId, initialTimeConstraint, projectData }) => {
  const [weeklySchedule, setWeeklySchedule] = useState<any>(DEFAULT_SCHEDULE);
  const [holidays, setHolidays] = useState<string[]>([]);
  const [newHoliday, setNewHoliday] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (initialTimeConstraint) {
        setWeeklySchedule(normalizeWeeklySchedule(initialTimeConstraint.weekly_schedule));
        setHolidays(initialTimeConstraint.holidays_list || []);
      } else {
        setWeeklySchedule(DEFAULT_SCHEDULE);
        setHolidays([]);
      }
    }
  }, [isOpen, initialTimeConstraint]);

  // Calculate total weekly working hours dynamically from shift intervals
  const totalWeeklyHours = React.useMemo(() => {
    let sum = 0;
    DAYS.forEach(day => {
      const intervals = weeklySchedule[day] || [];
      intervals.forEach((inv: string) => {
        const parts = inv.split('-');
        if (parts.length === 2) {
          const [sH, sM] = parts[0].split(':').map(Number);
          const [eH, eM] = parts[1].split(':').map(Number);
          let startMin = (sH || 0) * 60 + (sM || 0);
          let endMin = (eH || 0) * 60 + (eM || 0);
          if (endMin < startMin) endMin += 24 * 60; // night shift overlap
          sum += (endMin - startMin) / 60;
        }
      });
    });
    return sum;
  }, [weeklySchedule]);

  if (!isOpen) return null;

  const handleSave = async () => {
    try {
      setSaving(true);
      const payload = {
        weekly_schedule: weeklySchedule,
        holidays_list: holidays
      };
      if (initialTimeConstraint?.id) {
        await api.updateTimeConstraint(projectId, payload);
      } else {
        await api.createTimeConstraint(projectId, payload);
      }

      onClose(true);
    } catch (err) {
      alert("Failed to save calendar: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleAddHoliday = () => {
    if (newHoliday && !holidays.includes(newHoliday)) {
      setHolidays([...holidays, newHoliday]);
      setNewHoliday('');
    }
  };

  const removeHoliday = (h: string) => {
    setHolidays(holidays.filter(x => x !== h));
  };

  const addSchedule = (day: string, start: string, end: string) => {
    if (!start || !end) return;

    const parseTime = (t: string) => {
      const [h, m] = t.split(':').map(Number);
      return h * 60 + (m || 0);
    };

    const startMins = parseTime(start);
    const endMins = parseTime(end);

    if (startMins >= endMins) {
      alert("Invalid Shift: End time must be after start time.");
      return;
    }

    const current = weeklySchedule[day] || [];

    // Check for overlaps
    for (const inv of current) {
      const [invS, invE] = inv.split('-');
      const invStartMins = parseTime(invS);
      const invEndMins = parseTime(invE);

      if (startMins < invEndMins && endMins > invStartMins) {
        alert(`Overlap Error: This shift overlaps with existing shift (${inv}).`);
        return;
      }
    }

    const interval = `${start}-${end}`;
    const newShifts = [...current, interval].sort((a, b) => {
      return parseTime(a.split('-')[0]) - parseTime(b.split('-')[0]);
    });

    setWeeklySchedule({ ...weeklySchedule, [day]: newShifts });
  };

  const removeSchedule = (day: string, index: number) => {
    const newArr = [...(weeklySchedule[day] || [])];
    newArr.splice(index, 1);
    setWeeklySchedule({ ...weeklySchedule, [day]: newArr });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white w-full max-w-6xl rounded-xl shadow-2xl flex flex-col max-h-[95vh] h-full">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 rounded-t-xl shrink-0">
          <div className="flex items-center">
            <div className="bg-indigo-100 p-2 rounded-lg mr-3">
              <Calendar size={20} className="text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Agenda</h2>
              <p className="text-xs text-slate-500">Configure working hours, holidays, and overtime rules.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-white custom-scrollbar">
          <div className="grid grid-cols-5 gap-6">
            <div className="col-span-4">
              <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center">
                <Clock size={16} className="mr-2 text-slate-500" /> Weekly Working Hours
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
                {DAYS.map(day => (
                  <DayScheduleRow
                    key={day}
                    day={day}
                    intervals={weeklySchedule[day] || []}
                    onAdd={(start: string, end: string) => addSchedule(day, start, end)}
                    onRemove={(idx: number) => removeSchedule(day, idx)}
                  />
                ))}
              </div>
            </div>

            <div className="col-span-1 border-l border-slate-200 pl-6">
              <h3 className="text-sm font-bold text-slate-800 mb-3">Holidays</h3>
              <div className="flex flex-col gap-2 mb-4">
                <input
                  type="date"
                  value={newHoliday}
                  onChange={e => setNewHoliday(e.target.value)}
                  className="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={handleAddHoliday}
                  className="w-full justify-center bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-3 py-2 rounded text-sm font-medium flex items-center transition"
                >
                  <Plus size={14} className="mr-1" /> Add
                </button>
              </div>

              {holidays.length > 0 ? (
                <div className="flex flex-col gap-2">
                  {holidays.sort().map(h => (
                    <div key={h} className="bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-md text-xs font-medium text-slate-700 flex items-center justify-between">
                      {h}
                      <button onClick={() => removeHoliday(h)} className="ml-2 text-slate-400 hover:text-red-500 transition">
                        <X size={14} strokeWidth={2.5} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No holidays.</p>
              )}
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-slate-200 flex justify-end gap-3 bg-slate-50 rounded-b-xl shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors shadow-sm flex items-center disabled:opacity-50"
          >
            <Save size={16} className="mr-2" />
            {saving ? 'Saving...' : 'Save Calendar'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TimeManagerModal;
