import { useTranslation } from "react-i18next";

const LANGS = ["gu", "hi", "en"];

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation();

  return (
    <div className="flex items-center rounded-full bg-slate-100 p-0.5">
      {LANGS.map((lng) => (
        <button
          key={lng}
          onClick={() => i18n.changeLanguage(lng)}
          className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
            i18n.language === lng
              ? "bg-navy-900 text-white shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          {t(`languages.${lng}`)}
        </button>
      ))}
    </div>
  );
}
