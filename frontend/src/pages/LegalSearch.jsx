import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Search, Sparkles } from "lucide-react";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Spinner from "../components/ui/Spinner";
import Textarea from "../components/ui/Textarea";
import LegalSuggestions from "../components/legal/LegalSuggestions";
import SectionCard from "../components/legal/SectionCard";
import { useLegalSearch, useSuggestSections } from "../hooks/useLegal";
import { toast } from "../store/uiStore";

export default function LegalSearch() {
  const { t } = useTranslation();

  const [qInput, setQInput] = useState("");
  const [actInput, setActInput] = useState("");
  const [committed, setCommitted] = useState({ q: "", act: "" });
  const { data: results, isFetching } = useLegalSearch(committed.q, committed.act);

  const [narrative, setNarrative] = useState("");
  const [language, setLanguage] = useState("gu");
  const [suggestions, setSuggestions] = useState(null);
  const suggest = useSuggestSections();

  const runSuggest = () => {
    if (narrative.trim().length < 20) return;
    suggest.mutate(
      { narrative, language },
      {
        onSuccess: setSuggestions,
        onError: () => toast("error", t("legal.suggestFailed")),
      }
    );
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-bold text-slate-800">{t("legal.title")}</h1>
        <p className="text-xs text-slate-500">{t("legal.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-2">
        <Card title={t("legal.searchTitle")}>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setCommitted({ q: qInput, act: actInput });
            }}
          >
            <div className="flex-1">
              <Input
                placeholder={t("legal.searchPlaceholder")}
                value={qInput}
                onChange={(e) => setQInput(e.target.value)}
              />
            </div>
            <Select value={actInput} onChange={(e) => setActInput(e.target.value)} className="!w-28">
              <option value="">{t("legal.allActs")}</option>
              {["BNS", "BNSS", "BSA"].map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </Select>
            <Button type="submit">
              <Search size={14} />
              {t("legal.search")}
            </Button>
          </form>

          <div className="mt-4 space-y-3">
            {isFetching ? (
              <Spinner label={t("common.loading")} />
            ) : results && results.length > 0 ? (
              results.map((s) => <SectionCard key={`${s.act}-${s.section}`} section={s} />)
            ) : committed.q ? (
              <p className="py-4 text-center text-xs text-slate-400">{t("legal.noSections")}</p>
            ) : null}
          </div>
        </Card>

        <Card title={t("legal.suggestTitle")} subtitle={t("legal.suggestHint")}>
          <div className="space-y-3">
            <Select label={t("case.narrativeLanguage")} value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="gu">{t("languages.gu")}</option>
              <option value="hi">{t("languages.hi")}</option>
              <option value="en">{t("languages.en")}</option>
            </Select>
            <Textarea
              rows={5}
              placeholder={t("legal.narrativePlaceholder")}
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
            />
            <div className="flex justify-end">
              <Button onClick={runSuggest} loading={suggest.isPending} disabled={narrative.trim().length < 20}>
                <Sparkles size={14} />
                {suggest.isPending ? t("legal.suggesting") : t("legal.suggest")}
              </Button>
            </div>
            <div className="border-t border-slate-100 pt-4">
              <LegalSuggestions data={suggestions} />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
