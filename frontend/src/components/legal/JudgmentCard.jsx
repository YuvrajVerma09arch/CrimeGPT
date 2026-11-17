import { useTranslation } from "react-i18next";
import { Landmark } from "lucide-react";
import { relevancePercent } from "../../utils/format";

export default function JudgmentCard({ judgment }) {
  const { t } = useTranslation();

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 rounded-md bg-navy-50 p-1.5 text-navy-600">
          <Landmark size={14} />
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="text-[13px] font-semibold leading-snug text-slate-800">
            {judgment.title}
          </h4>
          <p className="mt-0.5 text-[11px] text-slate-400">
            {judgment.court} · {judgment.year}
            {judgment.relevance_score != null && (
              <>
                {" "}
                · {relevancePercent(judgment.relevance_score)}%{" "}
                {t("legal.relevance")}
              </>
            )}
          </p>
          <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-slate-500">
            {judgment.summary}
          </p>
        </div>
      </div>
    </div>
  );
}
