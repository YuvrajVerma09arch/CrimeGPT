import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  FilePlus2,
  LayoutDashboard,
  FolderOpen,
  Scale,
  ScrollText,
  Shield,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, key: "nav.dashboard", end: true },
  { to: "/cases/new", icon: FilePlus2, key: "nav.newCase" },
  { to: "/documents", icon: FolderOpen, key: "nav.documents" },
  { to: "/legal", icon: Scale, key: "nav.legal" },
  { to: "/audit", icon: ScrollText, key: "nav.audit" },
];

export default function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-navy-900 text-navy-100">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="rounded-md bg-amber-600 p-1.5 text-white">
          <Shield size={18} />
        </div>
        <div>
          <div className="text-[15px] font-bold tracking-tight text-white">
            {t("app.name")}
          </div>
          <div className="text-[10px] leading-tight text-navy-300">
            {t("app.org")}
          </div>
        </div>
      </div>

      <nav className="mt-2 flex-1 space-y-0.5 px-3">
        <div className="micro-label px-2 pb-1 !text-navy-400">{t("nav.main")}</div>
        {NAV_ITEMS.map(({ to, icon: Icon, key, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors ${
                isActive
                  ? "bg-navy-800 text-amber-400"
                  : "text-navy-200 hover:bg-navy-800/60 hover:text-white"
              }`
            }
          >
            <Icon size={16} />
            {t(key)}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 text-[10px] leading-relaxed text-navy-400">
        {t("app.tagline")}
      </div>
    </aside>
  );
}
