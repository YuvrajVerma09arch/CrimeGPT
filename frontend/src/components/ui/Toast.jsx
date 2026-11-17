import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import { useUiStore } from "../../store/uiStore";

const STYLES = {
  success: { icon: CheckCircle2, classes: "border-emerald-200 text-emerald-800" },
  error: { icon: XCircle, classes: "border-red-200 text-red-800" },
  info: { icon: Info, classes: "border-navy-200 text-navy-800" },
};

export default function ToastStack() {
  const { toasts, dismissToast } = useUiStore();
  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[60] flex w-80 flex-col gap-2">
      {toasts.map((t) => {
        const { icon: Icon, classes } = STYLES[t.type] || STYLES.info;
        return (
          <div
            key={t.id}
            className={`flex items-start gap-2 rounded-lg border bg-white px-3.5 py-3 text-sm shadow-lg ${classes}`}
          >
            <Icon size={16} className="mt-0.5 shrink-0" />
            <span className="flex-1">{t.message}</span>
            <button
              onClick={() => dismissToast(t.id)}
              className="text-slate-400 hover:text-slate-600"
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
