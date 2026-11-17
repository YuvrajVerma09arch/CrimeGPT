import { useTranslation } from "react-i18next";
import Badge from "../ui/Badge";
import { STATUS_COLORS } from "../../utils/format";

export default function StatusBadge({ status }) {
  const { t } = useTranslation();
  if (!status) return null;
  return (
    <Badge colorClasses={STATUS_COLORS[status]}>{t(`status.${status}`)}</Badge>
  );
}
