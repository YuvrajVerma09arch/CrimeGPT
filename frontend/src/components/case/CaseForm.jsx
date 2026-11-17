import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslation } from "react-i18next";
import { Sparkles } from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";
import Select from "../ui/Select";
import Textarea from "../ui/Textarea";

export default function CaseForm({ onSubmit, onAnalyze, analyzing, submitting }) {
  const { t } = useTranslation();

  const schema = z.object({
    fir_number: z.string().min(1, t("case.firNumberRequired")),
    station: z.string().min(1, t("case.stationRequired")),
    ps_name: z.string().optional(),
    incident_date: z.string().min(1, t("case.incidentDateRequired")),
    incident_time: z.string().optional(),
    incident_place: z.string().optional(),
    language: z.enum(["gu", "hi", "en"]),
    narrative: z.string().min(20, t("case.narrativeMin")),
  });

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { language: "gu" },
  });

  const analyze = () => {
    const { narrative, language } = getValues();
    if (narrative && narrative.trim().length >= 20) {
      onAnalyze(narrative, language);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Card title={t("case.detailsSection")}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label={t("case.firNumber")}
            placeholder="FIR/2026/0001"
            error={errors.fir_number?.message}
            {...register("fir_number")}
          />
          <Input
            label={t("case.station")}
            placeholder="Navrangpura"
            error={errors.station?.message}
            {...register("station")}
          />
          <Input
            label={t("case.psName")}
            hint={t("common.optional")}
            {...register("ps_name")}
          />
          <Input
            label={t("case.incidentPlace")}
            hint={t("common.optional")}
            {...register("incident_place")}
          />
          <Input
            type="date"
            label={t("case.incidentDate")}
            error={errors.incident_date?.message}
            {...register("incident_date")}
          />
          <Input
            type="time"
            label={t("case.incidentTime")}
            hint={t("common.optional")}
            {...register("incident_time")}
          />
        </div>

        <div className="mt-4 space-y-4">
          <Select label={t("case.narrativeLanguage")} {...register("language")}>
            <option value="gu">{t("languages.gu")}</option>
            <option value="hi">{t("languages.hi")}</option>
            <option value="en">{t("languages.en")}</option>
          </Select>
          <Textarea
            label={t("case.narrative")}
            rows={7}
            placeholder={t("case.narrativePlaceholder")}
            error={errors.narrative?.message}
            {...register("narrative")}
          />
          <div className="flex justify-end">
            <Button
              type="button"
              variant="secondary"
              loading={analyzing}
              onClick={analyze}
            >
              <Sparkles size={14} className="text-amber-600" />
              {analyzing ? t("case.analyzing") : t("case.analyze")}
            </Button>
          </div>
        </div>
      </Card>

      <div className="flex justify-end">
        <Button type="submit" size="lg" loading={submitting}>
          {submitting ? t("case.creating") : t("case.createCase")}
        </Button>
      </div>
    </form>
  );
}
