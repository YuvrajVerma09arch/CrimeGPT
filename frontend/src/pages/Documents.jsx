import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FolderOpen } from "lucide-react";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Select from "../components/ui/Select";
import DocumentList from "../components/documents/DocumentList";
import GenerateDocumentsPanel from "../components/documents/GenerateDocumentsPanel";
import { useCases } from "../hooks/useCases";

export default function Documents() {
  const { t } = useTranslation();
  const { data } = useCases({ page: 1, page_size: 100 });
  const [caseId, setCaseId] = useState("");

  const cases = data?.items || [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold text-slate-800">{t("documents.title")}</h1>
        <p className="text-xs text-slate-500">{t("documents.subtitle")}</p>
      </div>

      <Card title={t("documents.selectCase")}>
        <Select value={caseId} onChange={(e) => setCaseId(e.target.value)}>
          <option value="">{t("documents.selectCasePlaceholder")}</option>
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.fir_number} — {c.station}
            </option>
          ))}
        </Select>
      </Card>

      {caseId ? (
        <>
          <GenerateDocumentsPanel caseId={caseId} />
          <DocumentList caseId={caseId} />
        </>
      ) : (
        <EmptyState icon={FolderOpen} title={t("documents.pickHint")} />
      )}
    </div>
  );
}
