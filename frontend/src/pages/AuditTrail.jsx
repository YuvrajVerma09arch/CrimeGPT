import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import Select from "../components/ui/Select";
import AuditLog from "../components/audit/AuditLog";
import VersionDiff from "../components/audit/VersionDiff";
import { auditService } from "../services/auditService";

const TABLES = ["cases", "persons", "seized_items", "case_sections", "documents"];
const EMPTY_FILTERS = { case_id: "", table_name: "", date_from: "", date_to: "" };

export default function AuditTrail() {
  const { t } = useTranslation();
  const [form, setForm] = useState(EMPTY_FILTERS);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [diffEntry, setDiffEntry] = useState(null);

  const { data: entries, isLoading } = useQuery({
    queryKey: ["audit", filters],
    queryFn: () => auditService.query(filters),
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold text-slate-800">{t("audit.title")}</h1>
        <p className="text-xs text-slate-500">{t("audit.subtitle")}</p>
      </div>

      <Card>
        <form
          className="grid grid-cols-2 items-end gap-3 lg:grid-cols-6"
          onSubmit={(e) => {
            e.preventDefault();
            setFilters(form);
          }}
        >
          <div className="col-span-2">
            <Input
              label={t("audit.caseId")}
              placeholder={t("audit.caseIdPlaceholder")}
              value={form.case_id}
              onChange={(e) => set("case_id", e.target.value)}
            />
          </div>
          <Select label={t("audit.table")} value={form.table_name} onChange={(e) => set("table_name", e.target.value)}>
            <option value="">{t("audit.allTables")}</option>
            {TABLES.map((x) => (
              <option key={x} value={x}>{t(`audit.tables.${x}`)}</option>
            ))}
          </Select>
          <Input type="date" label={t("audit.dateFrom")} value={form.date_from} onChange={(e) => set("date_from", e.target.value)} />
          <Input type="date" label={t("audit.dateTo")} value={form.date_to} onChange={(e) => set("date_to", e.target.value)} />
          <div className="flex gap-2">
            <Button type="submit">{t("audit.applyFilters")}</Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setForm(EMPTY_FILTERS);
                setFilters(EMPTY_FILTERS);
              }}
            >
              {t("audit.clearFilters")}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <AuditLog entries={entries} loading={isLoading} onViewDiff={setDiffEntry} />
      </Card>

      <Modal open={Boolean(diffEntry)} onClose={() => setDiffEntry(null)} title={t("audit.diffTitle")} wide>
        {diffEntry && <VersionDiff oldData={diffEntry.old_data} newData={diffEntry.new_data} />}
      </Modal>
    </div>
  );
}
