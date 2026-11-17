import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LogOut } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { toast } from "../../store/uiStore";
import LanguageSwitcher from "./LanguageSwitcher";
import RoleBadge from "./RoleBadge";

export default function Navbar() {
  const { t } = useTranslation();
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await signOut();
    toast("info", t("toast.loggedOut"));
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-end gap-4 border-b border-slate-200 bg-white/95 px-6 backdrop-blur">
      <LanguageSwitcher />
      {user && (
        <div className="flex items-center gap-2.5 border-l border-slate-200 pl-4">
          <div className="text-right leading-tight">
            <div className="text-[13px] font-semibold text-slate-800">
              {user.name}
            </div>
            <div className="text-[11px] text-slate-400">{user.badge_no}</div>
          </div>
          <RoleBadge role={user.role} />
          <button
            onClick={onLogout}
            title={t("auth.logout")}
            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-red-600"
          >
            <LogOut size={16} />
          </button>
        </div>
      )}
    </header>
  );
}
