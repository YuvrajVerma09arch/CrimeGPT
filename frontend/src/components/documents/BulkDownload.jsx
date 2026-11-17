import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FolderArchive } from "lucide-react";
import Button from "../ui/Button";
import { documentService } from "../../services/documentService";
import { toast } from "../../store/uiStore";

export default function BulkDownload({ caseId, disabled }) {
  const { t } = useTranslation();
  const [downloading, setDownloading] = useState(false);

  const run = async () => {
    setDownloading(true);
    try {
      await documentService.bulkDownload(caseId);
    } catch {
      toast("error", t("documents.downloadFailed"));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Button
      variant="secondary"
      size="sm"
      disabled={disabled}
      loading={downloading}
      onClick={run}
    >
      <FolderArchive size={13} />
      {downloading ? t("documents.downloading") : t("documents.bulkDownload")}
    </Button>
  );
}
