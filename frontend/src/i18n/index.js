import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./en.json";
import hi from "./hi.json";
import gu from "./gu.json";

const stored =
  typeof window !== "undefined" && window.localStorage
    ? window.localStorage.getItem("language")
    : null;

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
    gu: { translation: gu },
  },
  lng: stored || "gu",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  returnNull: false,
});

i18n.on("languageChanged", (lng) => {
  try {
    window.localStorage.setItem("language", lng);
  } catch {
    /* storage unavailable */
  }
});

export default i18n;
