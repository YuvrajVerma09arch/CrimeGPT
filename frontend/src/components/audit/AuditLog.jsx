import { useTranslation } from "react-i18next";
import { ScrollText } from "lucide-react";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import Spinner from "../ui/Spinner";
import { Table, THead, TRow, TCell } from "../ui/Table";
import { ACTION_COLORS, formatDateTime } from "../../utils/format";

export default function AuditLog({ entries, loading, onViewDiff }) {
  const { t } = useTranslation();

  if (loading) return <Spinner label={t("common.loading")} />;
  if (!entries || entries.length === 0) {
    return <EmptyState icon={ScrollText} title={t("audit.none")} />;
  }

  return (
    <Table>
      <THead
        columns={[
          t("audit.action"),
          t("audit.table"),
          t("audit.record"),
          t("audit.changedBy"),
          t("audit.changedAt"),
          "",
        ]}
      />
      <tbody>
        {entries.map((e) => (
          <TRow key={e.id}>
            <TCell>
              <Badge colorClasses={ACTION_COLORS[e.action]}>
                {t(`audit.actions.${e.action}`, e.action)}
              </Badge>
            </TCell>
            <TCell className="text-slate-600">
              {t(`audit.tables.${e.table_name}`, e.table_name)}
            </TCell>
            <TCell>
              <span className="font-mono text-[11px] text-slate-400">
                {e.record_id ? `${e.record_id.slice(0, 8)}…` : "—"}
              </span>
            </TCell>
            <TCell>{e.user?.name || t("common.none")}</TCell>
            <TCell className="tabular-nums text-slate-500">
              {formatDateTime(e.changed_at)}
            </TCell>
            <TCell>
              {(e.old_data || e.new_data) && (
                <Button variant="ghost" size="sm" onClick={() => onViewDiff(e)}>
                  {t("audit.viewDiff")}
                </Button>
              )}
            </TCell>
          </TRow>
        ))}
      </tbody>
    </Table>
  );
}
