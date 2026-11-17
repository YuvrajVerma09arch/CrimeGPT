import { useTranslation } from "react-i18next";
import Badge from "../ui/Badge";
import { ROLE_COLORS } from "../../utils/format";

export default function RoleBadge({ role }) {
  const { t } = useTranslation();
  if (!role) return null;
  return (
    <Badge colorClasses={ROLE_COLORS[role]}>{t(`roles.${role}`)}</Badge>
  );
}
