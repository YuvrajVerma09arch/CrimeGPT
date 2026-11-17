import { Loader2 } from "lucide-react";

export default function Spinner({ label, className = "" }) {
  return (
    <div
      className={`flex items-center justify-center gap-2 py-10 text-sm text-slate-500 ${className}`}
    >
      <Loader2 size={18} className="animate-spin text-amber-600" />
      {label}
    </div>
  );
}
