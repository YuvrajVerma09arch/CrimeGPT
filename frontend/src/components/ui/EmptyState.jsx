import { Inbox } from "lucide-react";

export default function EmptyState({ icon: Icon = Inbox, title, hint, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      <div className="rounded-full bg-slate-100 p-3 text-slate-400">
        <Icon size={22} />
      </div>
      <p className="text-sm font-medium text-slate-600">{title}</p>
      {hint && <p className="max-w-xs text-xs text-slate-400">{hint}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
