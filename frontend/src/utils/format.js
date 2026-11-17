import { format, parseISO } from "date-fns";

function toDate(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  try {
    return parseISO(value);
  } catch {
    return null;
  }
}

export function formatDate(value) {
  const d = toDate(value);
  return d ? format(d, "dd MMM yyyy") : "—";
}

export function formatDateTime(value) {
  const d = toDate(value);
  return d ? format(d, "dd MMM yyyy, HH:mm") : "—";
}

export const STATUS_COLORS = {
  OPEN: "bg-blue-50 text-blue-700 ring-blue-200",
  ARRESTED: "bg-amber-50 text-amber-700 ring-amber-200",
  CHARGESHEETED: "bg-purple-50 text-purple-700 ring-purple-200",
  CLOSED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export const ACTION_COLORS = {
  INSERT: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  UPDATE: "bg-amber-50 text-amber-700 ring-amber-200",
  DELETE: "bg-red-50 text-red-700 ring-red-200",
};

export const ROLE_COLORS = {
  IO: "bg-slate-100 text-slate-700 ring-slate-300",
  SHO: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  LEGAL_ADVISOR: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export const ACT_COLORS = {
  BNS: "bg-navy-50 text-navy-700 ring-navy-200",
  BNSS: "bg-cyan-50 text-cyan-700 ring-cyan-200",
  BSA: "bg-fuchsia-50 text-fuchsia-700 ring-fuchsia-200",
  IPC: "bg-slate-100 text-slate-600 ring-slate-300",
  CrPC: "bg-slate-100 text-slate-600 ring-slate-300",
};

export function relevancePercent(score) {
  return Math.round(Math.max(0, Math.min(1, score ?? 0)) * 100);
}
