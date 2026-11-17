import { Navigate, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useLoadUser } from "../../hooks/useAuth";
import Spinner from "../ui/Spinner";

export default function ProtectedRoute() {
  const { t } = useTranslation();
  const { loading, authenticated } = useLoadUser();

  if (!authenticated) return <Navigate to="/login" replace />;
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label={t("app.loading")} />
      </div>
    );
  }
  return <Outlet />;
}
