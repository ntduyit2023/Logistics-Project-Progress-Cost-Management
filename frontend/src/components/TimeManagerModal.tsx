import React, { useState, useEffect } from 'react';
import { X, Calendar, Plus, Save, Clock } from 'lucide-react';
import { api } from '../services/api';

interface TimeManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: number | string;
  initialTimeConstraint: any;
}

const DEFAULT_SCHEDULE = {
  monday: ["08:00-12:00", "13:00-17:00"],
  tuesday: ["08:00-12:00", "13:00-17:00"],
  wednesday: ["08:00-12:00", "13:00-17:00"],
  thursday: ["08:00-12:00", "13:00-17:00"],
  friday: ["08:00-12:00", "13:00-17:00"],
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

const DayScheduleRow = ({ day, intervals, onAdd, onRemove }: any) => {
  const [start, setStart] = useState("08:00");
  const [end, setEnd] = useState("12:00");

  return (
    <tr className="bg-white">
      <td className="px-4 py-3 font-medium text-slate-700 capitalize w-1/5">{day}</td>
      <td className="px-4 py-3">
        <div className="flex flex-col gap-2">
          {/* List of existing intervals */}
          <div className="flex flex-wrap gap-2 items-center">
            {Array.isArray(intervals) && intervals.map((interval: string, idx: number) => (
              <div key={idx} className="bg-indigo-50 border border-indigo-100 px-2 py-1 rounded text-xs font-medium text-indigo-700 flex items-center shadow-sm">
                {interval}
                <button onClick={() => onRemove(idx)} className="ml-1.5 text-indigo-400 hover:text-red-500 transition focus:outline-none">
                  <X size={12} strokeWidth={3} />
                </button>
              </div>
            ))}
            {(!Array.isArray(intervals) || intervals.length === 0) && <span className="text-xs text-slate-400 italic">No shifts (Day off)</span>}
          </div>
          
          {/* Add custom interval inline */}
          <div className="flex items-center gap-2 mt-1 bg-slate-50 p-1.5 rounded-md border border-slate-200 w-fit">
            <input 
              type="time" 
              value={start} 
              onChange={e => setStart(e.target.value)} 
              className="border border-slate-300 rounded px-2 py-1 text-xs focus:outline-none focus:border-indigo-500 bg-white" 
            />
            <span className="text-slate-400 text-xs font-medium">to</span>
            <input 
              type="time" 
              value={end} 
              onChange={e => setEnd(e.target.value)} 
              className="border border-slate-300 rounded px-2 py-1 text-xs focus:outline-none focus:border-indigo-500 bg-white" 
            />
            <button 
              onClick={() => { onAdd(start, end); }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-2 py-1 rounded text-xs font-bold transition-colors shadow-sm ml-1"
            >
              + Add Shift
            </button>
          </div>
        </div>
      </td>
    </tr>
  );
};

const TimeManagerModal: React.FC<TimeManagerModalProps> = ({ isOpen, onClose, projectId, initialTimeConstraint }) => {
  const [weeklySchedule, setWeeklySchedule] = useState<any>(DEFAULT_SCHEDULE);
  const [overtimeMultiplier, setOvertimeMultiplier] = useState(1.5);
  const [holidays, setHolidays] = useState<string[]>([]);
  const [newHoliday, setNewHoliday] = useState('');
  const [saving, setSaving] = useState(false);

  const [targetDeadline, setTargetDeadline] = useState("2011-06-30 17:00:00");
  const [penaltyPerDay, setPenaltyPerDay] = useState(500.0);
  const [bonusPerDay, setBonusPerDay] = useState(200.0);

  useEffect(() => {
    if (isOpen && initialTimeConstraint) {
      setWeeklySchedule(normalizeWeeklySchedule(initialTimeConstraint.weekly_schedule));
      setOvertimeMultiplier(initialTimeConstraint.overtime_multiplier || 1.5);
      setHolidays(initialTimeConstraint.holidays_list || []);
      if (initialTimeConstraint.global_deadline) setTargetDeadline(initialTimeConstraint.global_deadline);
      if (initialTimeConstraint.penalty_per_day !== undefined) setPenaltyPerDay(initialTimeConstraint.penalty_per_day);
      if (initialTimeConstraint.bonus_per_day !== undefined) setBonusPerDay(initialTimeConstraint.bonus_per_day);
    } else if (isOpen) {
      setWeeklySchedule(DEFAULT_SCHEDULE);
      setOvertimeMultiplier(1.5);
      setHolidays([]);
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
      if (overtimeMultiplier < 1.0 || isNaN(overtimeMultiplier)) {
        alert("Overtime Multiplier must be at least 1.0");
        return;
      }
      setSaving(true);
      const payload = {
        weekly_schedule: weeklySchedule,
        holidays_list: holidays,
        overtime_multiplier: overtimeMultiplier,
        global_deadline: targetDeadline,
        penalty_per_day: Number(penaltyPerDay),
        bonus_per_day: Number(bonusPerDay)
      };
      if (initialTimeConstraint?.id) {
        await api.updateTimeConstraint(projectId, payload);
      } else {
        await api.createTimeConstraint(projectId, payload);
      }
      onClose();
      window.location.reload();
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
    const interval = `${start}-${end}`;
    const current = weeklySchedule[day] || [];
    if (!current.includes(interval)) {
      setWeeklySchedule({ ...weeklySchedule, [day]: [...current, interval] });
    }
  };

  const removeSchedule = (day: string, index: number) => {
    const newArr = [...(weeklySchedule[day] || [])];
    newArr.splice(index, 1);
    setWeeklySchedule({ ...weeklySchedule, [day]: newArr });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white w-full max-w-3xl rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 rounded-t-xl shrink-0">
          <div className="flex items-center">
            <div className="bg-indigo-100 p-2 rounded-lg mr-3">
              <Calendar size={20} className="text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">Project Calendar & Time Constraints</h2>
              <p className="text-xs text-slate-500">Configure working hours, holidays, and overtime rules.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-white custom-scrollbar space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
              <Clock size={16} className="mr-2 text-slate-500" /> Weekly Working Hours
            </h3>
            <div className="bg-slate-50 border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-100 text-slate-600">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Day</th>
                    <th className="px-4 py-2 font-semibold">Working Intervals</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {DAYS.map(day => (
                    <DayScheduleRow 
                      key={day}
                      day={day}
                      intervals={weeklySchedule[day] || []}
                      onAdd={(start: string, end: string) => addSchedule(day, start, end)}
                      onRemove={(idx: number) => removeSchedule(day, idx)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>



          <div>
            <h3 className="text-sm font-bold text-slate-800 mb-3">Holidays / Non-working Days</h3>
            <div className="flex gap-2 mb-3">
              <input 
                type="date" 
                value={newHoliday}
                onChange={e => setNewHoliday(e.target.value)}
                className="border border-slate-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
              <button 
                onClick={handleAddHoliday}
                className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-3 py-1.5 rounded text-sm font-medium flex items-center transition"
              >
                <Plus size={14} className="mr-1" /> Add Holiday
              </button>
            </div>
            
            {holidays.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {holidays.sort().map(h => (
                  <div key={h} className="bg-slate-100 border border-slate-200 px-3 py-1 rounded-full text-xs font-medium text-slate-700 flex items-center">
                    {h}
                    <button onClick={() => removeHoliday(h)} className="ml-2 text-slate-400 hover:text-red-500 transition">
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No holidays configured.</p>
            )}
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
