import { useTranslation } from "react-i18next";
import { Plus, Trash2 } from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";

const EMPTY_ITEM = {
  item_name: "",
  quantity: "",
  description: "",
  seized_from: "",
};

export default function ItemEditor({ items, onChange }) {
  const { t } = useTranslation();

  const update = (index, field, value) => {
    onChange(items.map((it, i) => (i === index ? { ...it, [field]: value } : it)));
  };

  return (
    <Card
      title={t("items.title")}
      subtitle={t("items.subtitle")}
      actions={
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => onChange([...items, { ...EMPTY_ITEM }])}
        >
          <Plus size={14} />
          {t("items.addItem")}
        </Button>
      }
    >
      {items.length === 0 ? (
        <p className="py-2 text-center text-xs text-slate-400">
          {t("items.none")}
        </p>
      ) : (
        <div className="space-y-3">
          {items.map((it, i) => (
            <div
              key={i}
              className="grid grid-cols-2 items-end gap-3 rounded-md border border-slate-200 bg-slate-50/60 p-3 sm:grid-cols-5"
            >
              <Input
                label={t("items.itemName")}
                value={it.item_name}
                onChange={(e) => update(i, "item_name", e.target.value)}
              />
              <Input
                label={t("items.quantity")}
                value={it.quantity}
                onChange={(e) => update(i, "quantity", e.target.value)}
              />
              <Input
                label={t("items.description")}
                value={it.description}
                onChange={(e) => update(i, "description", e.target.value)}
              />
              <Input
                label={t("items.seizedFrom")}
                value={it.seized_from}
                onChange={(e) => update(i, "seized_from", e.target.value)}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="!text-red-600"
                onClick={() => onChange(items.filter((_, x) => x !== i))}
              >
                <Trash2 size={13} />
                {t("items.remove")}
              </Button>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export { EMPTY_ITEM };
