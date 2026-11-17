import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Input from "../components/ui/Input";
import Modal from "../components/ui/Modal";
import Select from "../components/ui/Select";
import Spinner from "../components/ui/Spinner";
import { Table, THead, TRow, TCell } from "../components/ui/Table";
import AuditLog from "../components/audit/AuditLog";
import VersionDiff from "../components/audit/VersionDiff";
import CaseDiary from "../components/case/CaseDiary";
import StatusBadge from "../components/case/StatusBadge";
import DocumentList from "../components/documents/DocumentList";
import GenerateDocumentsPanel from "../components/documents/GenerateDocumentsPanel";
import { ACT_COLORS, formatDate, formatDateTime } from "../utils/format";
import { caseService } from "../services/caseService";
import { auditService } from "../services/auditService";
import { useCase, useCaseChildMutation, useDeleteCase, useUpdateCase } from "../hooks/useCases";
import { useAuthStore } from "../store/authStore";
import { toast } from "../store/uiStore";

const STATUSES = ["OPEN", "ARRESTED", "CHARGESHEETED", "CLOSED"];
const EMPTY_PERSON_FORM = {
  role: "ACCUSED",
  name: "",
  age: "",
  gender: "",
  phone: "",
  address: "",
  id_type: "",
  id_number: "",
};
const orNull = (v) => (v && String(v).trim() ? v : null);

function PersonModal({ open, onClose, initial, onSave, saving }) {
  const { t } = useTranslation();
  const [form, setForm] = useState(initial);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  // Re-seed the form whenever a different person is opened
  const [seedKey, setSeedKey] = useState(null);
  const currentKey = initial?.id || "new";
  if (open && seedKey !== currentKey) {
    setSeedKey(currentKey);
    setForm(initial);
  }

  if (!open) return null;
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={initial?.id ? t("persons.editPerson") : t("persons.addPerson")}
    >
      <div className="grid grid-cols-2 gap-3">
        <Select label={t("persons.role")} value={form.role} onChange={(e) => set("role", e.target.value)}>
          {["VICTIM", "ACCUSED", "WITNESS"].map((r) => (
            <option key={r} value={r}>{t(`persons.roles.${r}`)}</option>
          ))}
        </Select>
        <Input label={t("persons.name")} value={form.name} onChange={(e) => set("name", e.target.value)} />
        <Input type="number" label={t("persons.age")} value={form.age ?? ""} onChange={(e) => set("age", e.target.value)} />
        <Select label={t("persons.gender")} value={form.gender || ""} onChange={(e) => set("gender", e.target.value)}>
          <option value="">{t("common.none")}</option>
          {["MALE", "FEMALE", "OTHER"].map((g) => (
            <option key={g} value={g}>{t(`persons.genders.${g}`)}</option>
          ))}
        </Select>
        <Input label={t("persons.phone")} value={form.phone || ""} onChange={(e) => set("phone", e.target.value)} />
        <Input label={t("persons.address")} value={form.address || ""} onChange={(e) => set("address", e.target.value)} />
        <Select label={t("persons.idType")} value={form.id_type || ""} onChange={(e) => set("id_type", e.target.value)}>
          <option value="">{t("common.none")}</option>
          {["AADHAAR", "PAN", "PASSPORT", "VOTER_ID", "DRIVING_LICENSE"].map((x) => (
            <option key={x} value={x}>{t(`persons.idTypes.${x}`)}</option>
          ))}
        </Select>
        <Input label={t("persons.idNumber")} value={form.id_number || ""} onChange={(e) => set("id_number", e.target.value)} />
      </div>
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>{t("common.cancel")}</Button>
        <Button
          loading={saving}
          disabled={!form.name?.trim()}
          onClick={() =>
            onSave({
              role: form.role,
              name: form.name.trim(),
              age: form.age ? Number(form.age) : null,
              gender: orNull(form.gender),
              phone: orNull(form.phone),
              address: orNull(form.address),
              id_type: orNull(form.id_type),
              id_number: orNull(form.id_number),
            })
          }
        >
          {t("common.save")}
        </Button>
      </div>
    </Modal>
  );
}

export default function CaseDetail() {
  const { t } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const { data: c, isLoading, isError } = useCase(id);
  const updateCase = useUpdateCase(id);
  const deleteCase = useDeleteCase();

  const [tab, setTab] = useState("overview");
  const [personModal, setPersonModal] = useState(null); // null | person-form seed
  const [itemForm, setItemForm] = useState(null);
  const [sectionForm, setSectionForm] = useState(null);
  const [diffEntry, setDiffEntry] = useState(null);

  const savePerson = useCaseChildMutation(id, ({ personId, payload }) =>
    personId
      ? caseService.updatePerson(id, personId, payload)
      : caseService.addPerson(id, payload)
  );
  const removePerson = useCaseChildMutation(id, (pid) => caseService.removePerson(id, pid));
  const addItem = useCaseChildMutation(id, (payload) => caseService.addItem(id, payload));
  const removeItem = useCaseChildMutation(id, (iid) => caseService.removeItem(id, iid));
  const addSection = useCaseChildMutation(id, (payload) => caseService.addSection(id, payload));
  const removeSection = useCaseChildMutation(id, (sid) => caseService.removeSection(id, sid));
  const addDiary = useCaseChildMutation(id, (payload) => caseService.addDiaryEntry(id, payload));

  const { data: auditEntries, isLoading: auditLoading } = useQuery({
    queryKey: ["audit", { case_id: id }],
    queryFn: () => auditService.query({ case_id: id }),
    enabled: tab === "audit",
  });

  if (isLoading) return <Spinner label={t("common.loading")} />;
  if (isError || !c) return <EmptyState title={t("case.notFound")} />;

  const canDelete = user && ["SHO", "LEGAL_ADVISOR"].includes(user.role);
  const TABS = ["overview", "documents", "diary", "audit"];

  const onStatusChange = (status) => {
    updateCase.mutate(
      { status },
      {
        onSuccess: () => toast("success", t("case.statusUpdated")),
        onError: () => toast("error", t("case.caseUpdateFailed")),
      }
    );
  };

  const onDelete = () => {
    if (!window.confirm(t("common.confirmDelete"))) return;
    deleteCase.mutate(id, {
      onSuccess: () => {
        toast("success", t("case.caseDeleted"));
        navigate("/");
      },
      onError: () => toast("error", t("case.caseDeleteFailed")),
    });
  };

  return (
    <div className="space-y-5">
      <Link to="/" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700">
        <ArrowLeft size={13} />
        {t("common.back")}
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-mono text-lg font-bold text-navy-800">{c.fir_number}</h1>
          <StatusBadge status={c.status} />
          {c.crime_type && (
            <Badge className="capitalize">{c.crime_type.replaceAll("_", " ")}</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Select value={c.status} onChange={(e) => onStatusChange(e.target.value)} className="!w-44">
            {STATUSES.map((s) => (
              <option key={s} value={s}>{t(`status.${s}`)}</option>
            ))}
          </Select>
          {canDelete && (
            <Button variant="danger" size="sm" onClick={onDelete} loading={deleteCase.isPending}>
              <Trash2 size={13} />
              {t("case.deleteCase")}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-2 rounded-lg border border-slate-200 bg-white p-4 text-[13px] shadow-sm sm:grid-cols-4">
        {[
          [t("case.station"), c.station],
          [t("case.psName"), c.ps_name || "—"],
          [t("case.incidentDate"), `${formatDate(c.incident_date)}${c.incident_time ? " · " + c.incident_time.slice(0, 5) : ""}`],
          [t("case.incidentPlace"), c.incident_place || "—"],
          [t("case.io"), c.io ? `${c.io.name} (${c.io.badge_no})` : "—"],
          [t("case.registeredOn"), formatDateTime(c.created_at)],
          [t("case.updatedOn"), formatDateTime(c.updated_at)],
          [t("case.narrativeLanguage"), t(`languages.${c.language}`)],
        ].map(([label, value]) => (
          <div key={label}>
            <div className="micro-label">{label}</div>
            <div className="mt-0.5 text-slate-700">{value}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((x) => (
          <button
            key={x}
            onClick={() => setTab(x)}
            className={`-mb-px border-b-2 px-3.5 py-2 text-[13px] font-medium transition-colors ${
              tab === x
                ? "border-amber-600 text-amber-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t(`case.tabs.${x}`)}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="space-y-4">
          <Card title={t("case.narrative")}>
            <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-700">{c.narrative}</p>
            {c.narrative_en && c.language !== "en" && (
              <div className="mt-4 border-t border-slate-100 pt-3">
                <div className="micro-label mb-1">{t("case.narrativeEn")}</div>
                <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-500">{c.narrative_en}</p>
              </div>
            )}
          </Card>

          <Card
            title={t("persons.title")}
            actions={
              <Button variant="secondary" size="sm" onClick={() => setPersonModal({ ...EMPTY_PERSON_FORM })}>
                <Plus size={13} />
                {t("persons.addPerson")}
              </Button>
            }
          >
            {c.persons.length === 0 ? (
              <p className="py-2 text-center text-xs text-slate-400">{t("persons.none")}</p>
            ) : (
              <Table>
                <THead columns={[t("persons.role"), t("persons.name"), t("persons.age"), t("persons.phone"), t("persons.address"), t("common.actions")]} />
                <tbody>
                  {c.persons.map((p) => (
                    <TRow key={p.id}>
                      <TCell><Badge>{t(`persons.roles.${p.role}`)}</Badge></TCell>
                      <TCell className="font-medium text-slate-800">{p.name}</TCell>
                      <TCell>{p.age ?? "—"}</TCell>
                      <TCell>{p.phone || "—"}</TCell>
                      <TCell className="max-w-56 truncate">{p.address || "—"}</TCell>
                      <TCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" onClick={() => setPersonModal({ ...p, age: p.age ?? "" })}>
                            {t("common.edit")}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="!text-red-600"
                            onClick={() =>
                              removePerson.mutate(p.id, {
                                onSuccess: () => toast("success", t("persons.removed")),
                              })
                            }
                          >
                            {t("persons.remove")}
                          </Button>
                        </div>
                      </TCell>
                    </TRow>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>

          <Card
            title={t("items.title")}
            actions={
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setItemForm({ item_name: "", quantity: "", description: "", seized_from: "" })}
              >
                <Plus size={13} />
                {t("items.addItem")}
              </Button>
            }
          >
            {c.items.length === 0 ? (
              <p className="py-2 text-center text-xs text-slate-400">{t("items.none")}</p>
            ) : (
              <Table>
                <THead columns={[t("items.itemName"), t("items.quantity"), t("items.description"), t("items.seizedFrom"), ""]} />
                <tbody>
                  {c.items.map((it) => (
                    <TRow key={it.id}>
                      <TCell className="font-medium text-slate-800">{it.item_name}</TCell>
                      <TCell>{it.quantity || "—"}</TCell>
                      <TCell className="max-w-56 truncate">{it.description || "—"}</TCell>
                      <TCell>{it.seized_from || "—"}</TCell>
                      <TCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="!text-red-600"
                          onClick={() =>
                            removeItem.mutate(it.id, {
                              onSuccess: () => toast("success", t("items.removed")),
                            })
                          }
                        >
                          {t("items.remove")}
                        </Button>
                      </TCell>
                    </TRow>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>

          <Card
            title={t("sections.title")}
            subtitle={t("sections.subtitle")}
            actions={
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSectionForm({ act: "BNS", section: "", description: "" })}
              >
                <Plus size={13} />
                {t("sections.add")}
              </Button>
            }
          >
            {c.sections.length === 0 ? (
              <p className="py-2 text-center text-xs text-slate-400">{t("sections.none")}</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {c.sections.map((s) => (
                  <div key={s.id} className="flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5">
                    <Badge colorClasses={ACT_COLORS[s.act]}>{s.act}</Badge>
                    <span className="text-[13px] font-semibold tabular-nums text-slate-800">§{s.section}</span>
                    {s.description && (
                      <span className="max-w-52 truncate text-xs text-slate-500">{s.description}</span>
                    )}
                    <Badge>
                      {s.source === "AI_SUGGESTED" ? t("sections.aiSuggested") : t("sections.officerAdded")}
                    </Badge>
                    <button
                      className="text-slate-400 hover:text-red-600"
                      onClick={() =>
                        removeSection.mutate(s.id, {
                          onSuccess: () => toast("success", t("sections.removed")),
                        })
                      }
                      aria-label={t("common.delete")}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {tab === "documents" && (
        <div className="space-y-4">
          <GenerateDocumentsPanel caseId={id} />
          <DocumentList caseId={id} />
        </div>
      )}

      {tab === "diary" && (
        <CaseDiary
          entries={c.diary_entries}
          adding={addDiary.isPending}
          onAdd={(payload) =>
            addDiary.mutate(payload, {
              onSuccess: () => toast("success", t("diary.entryAdded")),
              onError: () => toast("error", t("diary.entryFailed")),
            })
          }
        />
      )}

      {tab === "audit" && (
        <Card title={t("audit.title")} subtitle={t("audit.subtitle")}>
          <AuditLog entries={auditEntries} loading={auditLoading} onViewDiff={setDiffEntry} />
        </Card>
      )}

      <PersonModal
        open={Boolean(personModal)}
        onClose={() => setPersonModal(null)}
        initial={personModal || EMPTY_PERSON_FORM}
        saving={savePerson.isPending}
        onSave={(payload) =>
          savePerson.mutate(
            { personId: personModal?.id, payload },
            {
              onSuccess: () => {
                toast("success", t("persons.updated"));
                setPersonModal(null);
              },
              onError: () => toast("error", t("persons.updateFailed")),
            }
          )
        }
      />

      <Modal open={Boolean(itemForm)} onClose={() => setItemForm(null)} title={t("items.addItem")}>
        {itemForm && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <Input label={t("items.itemName")} value={itemForm.item_name} onChange={(e) => setItemForm({ ...itemForm, item_name: e.target.value })} />
              <Input label={t("items.quantity")} value={itemForm.quantity} onChange={(e) => setItemForm({ ...itemForm, quantity: e.target.value })} />
              <Input label={t("items.description")} value={itemForm.description} onChange={(e) => setItemForm({ ...itemForm, description: e.target.value })} />
              <Input label={t("items.seizedFrom")} value={itemForm.seized_from} onChange={(e) => setItemForm({ ...itemForm, seized_from: e.target.value })} />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setItemForm(null)}>{t("common.cancel")}</Button>
              <Button
                loading={addItem.isPending}
                disabled={!itemForm.item_name.trim()}
                onClick={() =>
                  addItem.mutate(
                    {
                      item_name: itemForm.item_name.trim(),
                      quantity: orNull(itemForm.quantity),
                      description: orNull(itemForm.description),
                      seized_from: orNull(itemForm.seized_from),
                    },
                    { onSuccess: () => setItemForm(null) }
                  )
                }
              >
                {t("common.add")}
              </Button>
            </div>
          </>
        )}
      </Modal>

      <Modal open={Boolean(sectionForm)} onClose={() => setSectionForm(null)} title={t("sections.add")}>
        {sectionForm && (
          <>
            <div className="grid grid-cols-3 gap-3">
              <Select label={t("sections.act")} value={sectionForm.act} onChange={(e) => setSectionForm({ ...sectionForm, act: e.target.value })}>
                {["BNS", "BNSS", "BSA", "IPC", "CrPC"].map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </Select>
              <Input label={t("sections.section")} placeholder={t("sections.sectionPlaceholder")} value={sectionForm.section} onChange={(e) => setSectionForm({ ...sectionForm, section: e.target.value })} />
              <Input label={t("sections.description")} value={sectionForm.description} onChange={(e) => setSectionForm({ ...sectionForm, description: e.target.value })} />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setSectionForm(null)}>{t("common.cancel")}</Button>
              <Button
                loading={addSection.isPending}
                disabled={!sectionForm.section.trim()}
                onClick={() =>
                  addSection.mutate(
                    {
                      act: sectionForm.act,
                      section: sectionForm.section.trim(),
                      description: orNull(sectionForm.description),
                      source: "OFFICER_ADDED",
                    },
                    {
                      onSuccess: () => {
                        toast("success", t("sections.added"));
                        setSectionForm(null);
                      },
                    }
                  )
                }
              >
                {t("common.add")}
              </Button>
            </div>
          </>
        )}
      </Modal>

      <Modal open={Boolean(diffEntry)} onClose={() => setDiffEntry(null)} title={t("audit.diffTitle")} wide>
        {diffEntry && <VersionDiff oldData={diffEntry.old_data} newData={diffEntry.new_data} />}
      </Modal>
    </div>
  );
}
