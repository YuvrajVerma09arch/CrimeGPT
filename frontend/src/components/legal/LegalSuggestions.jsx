import { useTranslation } from "react-i18next";
import { Sparkles } from "lucide-react";
import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";
import JudgmentCard from "./JudgmentCard";
import SectionCard from "./SectionCard";

export default function LegalSuggestions({ data, onAddSection, addedKeys = new Set() }) {
  const { t } = useTranslation();

  if (!data) {
    return (
      <EmptyState
        icon={Sparkles}
        title={t("legal.noSuggestions")}
        hint={t("legal.noSuggestionsHint")}
      />
    );
  }

  const entityGroups = Object.entries(data.entities || {}).filter(
    ([, values]) => values && values.length > 0
  );

  return (
    <div className="space-y-5">
      {entityGroups.length > 0 && (
        <div>
          <h3 className="micro-label mb-2">{t("legal.entities")}</h3>
          <div className="space-y-1.5">
            {entityGroups.map(([group, values]) => (
              <div key={group} className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] text-slate-400">
                  {t(`legal.entityLabels.${group}`, group)}:
                </span>
                {values.map((v) => (
                  <Badge key={v}>{v}</Badge>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h3 className="micro-label mb-2">{t("legal.suggestions")}</h3>
        <div className="space-y-3">
          {(data.sections || []).map((s) => (
            <SectionCard
              key={`${s.act}-${s.section}`}
              section={s}
              onAdd={onAddSection}
              added={addedKeys.has(`${s.act}-${s.section}`)}
            />
          ))}
          {(data.sections || []).length === 0 && (
            <p className="text-xs text-slate-400">{t("legal.noSections")}</p>
          )}
        </div>
      </div>

      {(data.judgments || []).length > 0 && (
        <div>
          <h3 className="micro-label mb-2">{t("legal.judgments")}</h3>
          <div className="space-y-3">
            {data.judgments.map((j) => (
              <JudgmentCard key={j.title} judgment={j} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
