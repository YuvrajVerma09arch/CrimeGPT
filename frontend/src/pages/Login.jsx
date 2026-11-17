import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Shield } from "lucide-react";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import LanguageSwitcher from "../components/layout/LanguageSwitcher";
import { useAuth } from "../hooks/useAuth";

const DEMO_ACCOUNTS = [
  { badge: "IO001", role: "IO" },
  { badge: "SHO001", role: "SHO" },
  { badge: "LA001", role: "LEGAL_ADVISOR" },
];

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();

  const [badgeNo, setBadgeNo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!badgeNo.trim()) return setError(t("auth.badgeRequired"));
    if (!password) return setError(t("auth.passwordRequired"));
    setLoading(true);
    try {
      await login(badgeNo.trim(), password);
      navigate("/");
    } catch {
      setError(t("auth.loginFailed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-navy-950 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <div className="rounded-xl bg-amber-600 p-3 text-white shadow-lg">
            <Shield size={26} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            {t("app.name")}
          </h1>
          <p className="text-xs text-navy-300">{t("app.tagline")}</p>
          <p className="micro-label !text-navy-400">{t("app.org")}</p>
        </div>

        <form
          onSubmit={onSubmit}
          className="space-y-4 rounded-xl border border-navy-800 bg-white p-6 shadow-xl"
        >
          <div>
            <h2 className="text-sm font-semibold text-slate-800">
              {t("auth.signInTitle")}
            </h2>
            <p className="text-xs text-slate-400">{t("auth.signInSubtitle")}</p>
          </div>
          <Input
            label={t("auth.badgeNo")}
            placeholder={t("auth.badgePlaceholder")}
            value={badgeNo}
            onChange={(e) => setBadgeNo(e.target.value)}
            autoFocus
          />
          <Input
            type="password"
            label={t("auth.password")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p className="text-xs text-red-600">{error}</p>}
          <Button type="submit" className="w-full" size="lg" loading={loading}>
            {loading ? t("auth.signingIn") : t("auth.signIn")}
          </Button>

          <div className="rounded-md bg-slate-50 px-3 py-2.5 text-[11px] leading-relaxed text-slate-500">
            <span className="font-semibold text-slate-600">
              {t("auth.demoTitle")}:
            </span>{" "}
            {DEMO_ACCOUNTS.map((a, i) => (
              <span key={a.badge}>
                {i > 0 && " · "}
                <button
                  type="button"
                  className="font-mono font-semibold text-amber-700 underline-offset-2 hover:underline"
                  onClick={() => {
                    setBadgeNo(a.badge);
                    setPassword("demo123");
                  }}
                >
                  {a.badge}
                </button>{" "}
                ({t(`roles.${a.role}`)})
              </span>
            ))}
            <div className="mt-0.5">{t("auth.demoPassword")}</div>
          </div>
        </form>

        <div className="mt-4 flex justify-center">
          <LanguageSwitcher />
        </div>
      </div>
    </div>
  );
}
