export default function Badge({ colorClasses, className = "", children }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${
        colorClasses || "bg-slate-100 text-slate-600 ring-slate-300"
      } ${className}`}
    >
      {children}
    </span>
  );
}
