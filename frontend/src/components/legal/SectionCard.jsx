import { useTranslation } from "react-i18next";
import { Plus, Check } from "lucide-react";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import { ACT_COLORS, relevancePercent } from "../../utils/format";

export default function SectionCard({ section, onAdd, added }) {
  const { t } = useTranslation();
  const pct = relevancePercent(section.relevance_score);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge colorClasses={ACT_COLORS[section.act]}>{section.act}</Badge>
          <span className="text-sm font-bold tabular-nums text-slate-800">
            §{section.section}
          </span>
        </div>
        {onAdd && (
          <Button
            type="button"
            variant={added ? "ghost" : "secondary"}
            size="sm"
            disabled={added}
            onClick={() => onAdd(section)}
          >
            {added ? <Check size={13} className="text-emerald-600" /> : <Plus size={13} />}
            {added ? t("legal.addedToCase") : t("legal.addToCase")}
          </Button>
        )}
      </div>
      <h4 className="mt-1.5 text-[13px] font-semibold text-slate-800">
        {section.title}
      </h4>
      {(section.excerpt || section.text) && (
        <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-slate-500">
          {section.excerpt || section.text}
        </p>
      )}
      {section.relevance_score != null && (
        <div className="mt-3 flex items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-amber-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-[11px] font-medium tabular-nums text-slate-500">
            {pct}% {t("legal.relevance")}
          </span>
        </div>
      )}
    </div>
  );
}
