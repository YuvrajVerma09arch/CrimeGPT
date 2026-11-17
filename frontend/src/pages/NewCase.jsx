import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Card from "../components/ui/Card";
import CaseForm from "../components/case/CaseForm";
import ItemEditor from "../components/case/ItemEditor";
import PersonEditor from "../components/case/PersonEditor";
import LegalSuggestions from "../components/legal/LegalSuggestions";
import { useCreateCase } from "../hooks/useCases";
import { useSuggestSections } from "../hooks/useLegal";
import { useCaseStore } from "../store/caseStore";
import { toast } from "../store/uiStore";

const orNull = (v) => (v && String(v).trim() ? v : null);

export default function NewCase() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [persons, setPersons] = useState([]);
  const [items, setItems] = useState([]);

  const { suggestions, acceptedSections, setSuggestions, acceptSection, resetDraft } =
    useCaseStore();

  const suggest = useSuggestSections();
  const createCase = useCreateCase();

  const onAnalyze = (narrative, language) => {
    suggest.mutate(
      { narrative, language },
      {
        onSuccess: (data) => setSuggestions(data),
        onError: () => toast("error", t("legal.suggestFailed")),
      }
    );
  };

  const onSubmit = (v) => {
    const payload = {
      fir_number: v.fir_number.trim(),
      station: v.station.trim(),
      ps_name: orNull(v.ps_name),
      incident_date: v.incident_date,
      incident_time: orNull(v.incident_time),
      incident_place: orNull(v.incident_place),
      narrative: v.narrative,
      language: v.language,
      persons: persons
        .filter((p) => p.name.trim())
        .map((p) => ({
          role: p.role,
          name: p.name.trim(),
          age: p.age ? Number(p.age) : null,
          gender: orNull(p.gender),
          address: orNull(p.address),
          phone: orNull(p.phone),
          id_type: orNull(p.id_type),
          id_number: orNull(p.id_number),
        })),
      items: items
        .filter((it) => it.item_name.trim())
        .map((it) => ({
          item_name: it.item_name.trim(),
          quantity: orNull(it.quantity),
          description: orNull(it.description),
          seized_from: orNull(it.seized_from),
        })),
      sections: acceptedSections.map((s) => ({
        act: s.act,
        section: s.section,
        description: s.title,
        source: "AI_SUGGESTED",
        confidence: s.relevance_score ?? null,
      })),
    };

    createCase.mutate(payload, {
      onSuccess: (data) => {
        resetDraft();
        toast("success", t("case.caseCreated"));
        navigate(`/cases/${data.id}`);
      },
      onError: () => toast("error", t("case.caseCreateFailed")),
    });
  };

  const addedKeys = new Set(acceptedSections.map((s) => `${s.act}-${s.section}`));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-slate-800">
          {t("case.newCaseTitle")}
        </h1>
        <p className="text-xs text-slate-500">{t("case.newCaseSubtitle")}</p>
      </div>

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          <CaseForm
            onSubmit={onSubmit}
            onAnalyze={onAnalyze}
            analyzing={suggest.isPending}
            submitting={createCase.isPending}
          />
          <PersonEditor persons={persons} onChange={setPersons} />
          <ItemEditor items={items} onChange={setItems} />
        </div>

        <div className="xl:sticky xl:top-20">
          <Card title={t("legal.suggestions")}>
            <LegalSuggestions
              data={suggestions}
              onAddSection={(s) => {
                acceptSection(s);
                toast("success", t("sections.added"));
              }}
              addedKeys={addedKeys}
            />
          </Card>
        </div>
      </div>
    </div>
  );
}
