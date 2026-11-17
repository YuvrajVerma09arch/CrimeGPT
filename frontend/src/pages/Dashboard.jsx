import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { FilePlus2, FolderSearch, Gauge, Siren, FileCheck2, FolderOpen } from "lucide-react";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Spinner from "../components/ui/Spinner";
import { Table, THead, TRow, TCell } from "../components/ui/Table";
import StatusBadge from "../components/case/StatusBadge";
import { useCases, useSearchCases } from "../hooks/useCases";
import { formatDate } from "../utils/format";

function StatCard({ icon: Icon, label, value, accent }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`rounded-md p-2 ${accent}`}>
        <Icon size={18} />
      </div>
      <div>
        <div className="text-xl font-bold tabular-nums leading-none text-slate-800">
          {value}
        </div>
        <div className="micro-label mt-1">{label}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  const { data, isLoading } = useCases({ page: 1, page_size: 50 });
  const { data: searchResults, isFetching: searching } = useSearchCases(q);

  const items = data?.items || [];
  const count = (status) => items.filter((c) => c.status === status).length;
  const showSearch = q.trim().length >= 2;
  const rows = showSearch ? searchResults || [] : items.slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-800">
            {t("dashboard.title")}
          </h1>
          <p className="text-xs text-slate-500">{t("dashboard.subtitle")}</p>
        </div>
        <Link to="/cases/new">
          <Button>
            <FilePlus2 size={14} />
            {t("dashboard.registerCase")}
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          icon={Gauge}
          label={t("dashboard.totalCases")}
          value={data?.total ?? "—"}
          accent="bg-navy-50 text-navy-700"
        />
        <StatCard
          icon={FolderOpen}
          label={t("dashboard.open")}
          value={count("OPEN")}
          accent="bg-blue-50 text-blue-700"
        />
        <StatCard
          icon={Siren}
          label={t("dashboard.arrested")}
          value={count("ARRESTED")}
          accent="bg-amber-50 text-amber-700"
        />
        <StatCard
          icon={FileCheck2}
          label={t("dashboard.chargesheeted")}
          value={count("CHARGESHEETED")}
          accent="bg-purple-50 text-purple-700"
        />
      </div>

      <Card
        title={showSearch ? t("dashboard.searchResults") : t("dashboard.recentCases")}
        actions={
          <div className="w-72">
            <Input
              placeholder={t("dashboard.searchPlaceholder")}
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
        }
      >
        {isLoading || searching ? (
          <Spinner label={t("common.loading")} />
        ) : rows.length === 0 ? (
          <EmptyState
            icon={FolderSearch}
            title={showSearch ? t("dashboard.noResults") : t("dashboard.noCases")}
            hint={showSearch ? undefined : t("dashboard.noCasesHint")}
            action={
              showSearch ? undefined : (
                <Link to="/cases/new">
                  <Button variant="secondary" size="sm">
                    {t("dashboard.registerCase")}
                  </Button>
                </Link>
              )
            }
          />
        ) : (
          <Table>
            <THead
              columns={[
                t("case.firNumber"),
                t("case.station"),
                t("case.incidentDate"),
                t("case.crimeType"),
                t("case.status"),
                t("case.io"),
              ]}
            />
            <tbody>
              {rows.map((c) => (
                <TRow key={c.id} onClick={() => navigate(`/cases/${c.id}`)}>
                  <TCell className="font-mono text-[12px] font-semibold text-navy-700">
                    {c.fir_number}
                  </TCell>
                  <TCell>{c.station}</TCell>
                  <TCell>{formatDate(c.incident_date)}</TCell>
                  <TCell className="capitalize">
                    {c.crime_type ? c.crime_type.replaceAll("_", " ") : "—"}
                  </TCell>
                  <TCell>
                    <StatusBadge status={c.status} />
                  </TCell>
                  <TCell>{c.io?.name || "—"}</TCell>
                </TRow>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
