import { useTranslation } from "react-i18next";
import { Plus, Trash2 } from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";
import Select from "../ui/Select";

const EMPTY_PERSON = {
  role: "ACCUSED",
  name: "",
  age: "",
  gender: "",
  phone: "",
  address: "",
  id_type: "",
  id_number: "",
};

export default function PersonEditor({ persons, onChange }) {
  const { t } = useTranslation();

  const update = (index, field, value) => {
    onChange(
      persons.map((p, i) => (i === index ? { ...p, [field]: value } : p))
    );
  };

  return (
    <Card
      title={t("persons.title")}
      subtitle={t("persons.subtitle")}
      actions={
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => onChange([...persons, { ...EMPTY_PERSON }])}
        >
          <Plus size={14} />
          {t("persons.addPerson")}
        </Button>
      }
    >
      {persons.length === 0 ? (
        <p className="py-2 text-center text-xs text-slate-400">
          {t("persons.none")}
        </p>
      ) : (
        <div className="space-y-4">
          {persons.map((p, i) => (
            <div
              key={i}
              className="rounded-md border border-slate-200 bg-slate-50/60 p-3"
            >
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Select
                  label={t("persons.role")}
                  value={p.role}
                  onChange={(e) => update(i, "role", e.target.value)}
                >
                  {["VICTIM", "ACCUSED", "WITNESS"].map((r) => (
                    <option key={r} value={r}>
                      {t(`persons.roles.${r}`)}
                    </option>
                  ))}
                </Select>
                <Input
                  label={t("persons.name")}
                  value={p.name}
                  onChange={(e) => update(i, "name", e.target.value)}
                />
                <Input
                  type="number"
                  label={t("persons.age")}
                  value={p.age}
                  onChange={(e) => update(i, "age", e.target.value)}
                />
                <Select
                  label={t("persons.gender")}
                  value={p.gender}
                  onChange={(e) => update(i, "gender", e.target.value)}
                >
                  <option value="">{t("common.none")}</option>
                  {["MALE", "FEMALE", "OTHER"].map((g) => (
                    <option key={g} value={g}>
                      {t(`persons.genders.${g}`)}
                    </option>
                  ))}
                </Select>
                <Input
                  label={t("persons.phone")}
                  value={p.phone}
                  onChange={(e) => update(i, "phone", e.target.value)}
                />
                <Select
                  label={t("persons.idType")}
                  value={p.id_type}
                  onChange={(e) => update(i, "id_type", e.target.value)}
                >
                  <option value="">{t("common.none")}</option>
                  {["AADHAAR", "PAN", "PASSPORT", "VOTER_ID", "DRIVING_LICENSE"].map(
                    (x) => (
                      <option key={x} value={x}>
                        {t(`persons.idTypes.${x}`)}
                      </option>
                    )
                  )}
                </Select>
                <Input
                  label={t("persons.idNumber")}
                  value={p.id_number}
                  onChange={(e) => update(i, "id_number", e.target.value)}
                />
                <Input
                  label={t("persons.address")}
                  value={p.address}
                  onChange={(e) => update(i, "address", e.target.value)}
                />
              </div>
              <div className="mt-2 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="!text-red-600"
                  onClick={() => onChange(persons.filter((_, x) => x !== i))}
                >
                  <Trash2 size={13} />
                  {t("persons.remove")}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export { EMPTY_PERSON };
