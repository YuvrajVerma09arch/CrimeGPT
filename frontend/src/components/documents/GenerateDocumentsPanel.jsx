import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FileCog } from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import { DOC_TYPES } from "../../services/documentService";
import { useGenerateDocuments } from "../../hooks/useDocuments";
import { toast } from "../../store/uiStore";

export default function GenerateDocumentsPanel({ caseId }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState(new Set(DOC_TYPES));
  const generate = useGenerateDocuments(caseId);

  const toggle = (docType) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(docType)) next.delete(docType);
      else next.add(docType);
      return next;
    });
  };

  const run = () => {
    if (selected.size === 0) return;
    generate.mutate([...selected], {
      onSuccess: (data) => {
        if (data.status === "queued") toast("info", t("documents.queued"));
        else toast("success", t("documents.generated"));
      },
      onError: () => toast("error", t("documents.generateFailed")),
    });
  };

  return (
    <Card
      title={t("documents.generateTitle")}
      subtitle={t("documents.generateHint")}
      actions={
        <div className="flex gap-2 text-xs">
          <button
            type="button"
            className="text-slate-500 underline-offset-2 hover:underline"
            onClick={() => setSelected(new Set(DOC_TYPES))}
          >
            {t("documents.selectAll")}
          </button>
          <button
            type="button"
            className="text-slate-500 underline-offset-2 hover:underline"
            onClick={() => setSelected(new Set())}
          >
            {t("documents.clearAll")}
          </button>
        </div>
      }
    >
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {DOC_TYPES.map((docType) => (
          <label
            key={docType}
            className={`flex cursor-pointer items-center gap-2.5 rounded-md border px-3 py-2.5 text-[13px] transition-colors ${
              selected.has(docType)
                ? "border-amber-300 bg-amber-50/60 text-slate-800"
                : "border-slate-200 text-slate-500 hover:bg-slate-50"
            }`}
          >
            <input
              type="checkbox"
              checked={selected.has(docType)}
              onChange={() => toggle(docType)}
              className="h-3.5 w-3.5 rounded border-slate-300 text-amber-600 focus:ring-amber-500"
            />
            {t(`documents.types.${docType}`)}
          </label>
        ))}
      </div>
      <div className="mt-4 flex justify-end">
        <Button onClick={run} loading={generate.isPending} disabled={selected.size === 0}>
          <FileCog size={14} />
          {generate.isPending ? t("documents.generating") : t("documents.generate")}
        </Button>
      </div>
    </Card>
  );
}
