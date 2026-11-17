import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Archive,
  FileCheck2,
  FileText,
  MessageSquare,
  RefreshCcw,
  Siren,
  UserRound,
} from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";
import Select from "../ui/Select";
import Textarea from "../ui/Textarea";
import { formatDateTime } from "../../utils/format";

const TYPE_ICONS = {
  FIR_FILED: FileText,
  EVIDENCE_SEIZED: Archive,
  WITNESS_STATEMENT: UserRound,
  ARREST_MADE: Siren,
  DOCUMENT_GENERATED: FileCheck2,
  STATUS_CHANGED: RefreshCcw,
  NOTE: MessageSquare,
};

const ENTRY_TYPES = Object.keys(TYPE_ICONS);

export default function CaseDiary({ entries = [], onAdd, adding }) {
  const { t } = useTranslation();
  const [entryType, setEntryType] = useState("NOTE");
  const [description, setDescription] = useState("");

  const submit = () => {
    if (!description.trim()) return;
    onAdd({ entry_type: entryType, description: description.trim() });
    setDescription("");
  };

  return (
    <Card title={t("diary.title")} subtitle={t("diary.subtitle")}>
      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-[180px_1fr_auto] sm:items-end">
        <Select
          label={t("diary.entryType")}
          value={entryType}
          onChange={(e) => setEntryType(e.target.value)}
        >
          {ENTRY_TYPES.map((x) => (
            <option key={x} value={x}>
              {t(`diary.types.${x}`)}
            </option>
          ))}
        </Select>
        <Textarea
          label={t("diary.description")}
          rows={2}
          placeholder={t("diary.descriptionPlaceholder")}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Button type="button" onClick={submit} loading={adding}>
          {t("diary.addEntry")}
        </Button>
      </div>

      {entries.length === 0 ? (
        <EmptyState title={t("diary.none")} />
      ) : (
        <ol className="relative ml-3 space-y-5 border-l border-slate-200 pl-6">
          {entries.map((e) => {
            const Icon = TYPE_ICONS[e.entry_type] || MessageSquare;
            return (
              <li key={e.id} className="relative">
                <span className="absolute -left-[31px] rounded-full bg-white p-1 text-amber-600 ring-1 ring-slate-200">
                  <Icon size={12} />
                </span>
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="text-[13px] font-semibold text-slate-800">
                    {e.entry_type
                      ? t(`diary.types.${e.entry_type}`, e.entry_type)
                      : t("diary.types.NOTE")}
                  </span>
                  <span className="text-[11px] tabular-nums text-slate-400">
                    {formatDateTime(e.entry_date)}
                  </span>
                  {e.officer && (
                    <span className="text-[11px] text-slate-400">
                      · {e.officer.name}
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-[13px] leading-relaxed text-slate-600">
                  {e.description}
                </p>
              </li>
            );
          })}
        </ol>
      )}
    </Card>
  );
}
