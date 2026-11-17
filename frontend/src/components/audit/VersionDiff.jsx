import { useTranslation } from "react-i18next";

function renderValue(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function VersionDiff({ oldData, newData }) {
  const { t } = useTranslation();
  const keys = [
    ...new Set([...Object.keys(oldData || {}), ...Object.keys(newData || {})]),
  ].sort();

  const changedCount = keys.filter(
    (k) => renderValue(oldData?.[k]) !== renderValue(newData?.[k])
  ).length;

  return (
    <div>
      <p className="mb-3 text-xs text-slate-500">
        {t("audit.changedFields", { count: changedCount })}
      </p>
      <div className="overflow-hidden rounded-md border border-slate-200">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="micro-label px-3 py-2">{t("audit.field")}</th>
              <th className="micro-label px-3 py-2">{t("audit.oldValue")}</th>
              <th className="micro-label px-3 py-2">{t("audit.newValue")}</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((key) => {
              const oldV = renderValue(oldData?.[key]);
              const newV = renderValue(newData?.[key]);
              const changed = oldV !== newV;
              return (
                <tr
                  key={key}
                  className={`border-b border-slate-100 last:border-0 ${
                    changed ? "bg-amber-50/60" : ""
                  }`}
                >
                  <td className="px-3 py-2 font-medium text-slate-700">{key}</td>
                  <td className={`px-3 py-2 ${changed ? "text-red-700 line-through decoration-red-300" : "text-slate-500"}`}>
                    {oldV}
                  </td>
                  <td className={`px-3 py-2 ${changed ? "font-medium text-emerald-700" : "text-slate-500"}`}>
                    {newV}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
