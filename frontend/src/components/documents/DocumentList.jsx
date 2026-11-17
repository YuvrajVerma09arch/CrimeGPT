import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FileDown, FileText } from "lucide-react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";
import Spinner from "../ui/Spinner";
import { Table, THead, TRow, TCell } from "../ui/Table";
import BulkDownload from "./BulkDownload";
import { documentService } from "../../services/documentService";
import { useDocuments } from "../../hooks/useDocuments";
import { formatDateTime } from "../../utils/format";
import { toast } from "../../store/uiStore";

export default function DocumentList({ caseId }) {
  const { t } = useTranslation();
  const { data: documents, isLoading } = useDocuments(caseId);
  const [downloading, setDownloading] = useState(null);

  const download = async (doc, format) => {
    setDownloading(`${doc.id}-${format}`);
    try {
      await documentService.download(doc, format);
    } catch {
      toast("error", t("documents.downloadFailed"));
    } finally {
      setDownloading(null);
    }
  };

  return (
    <Card
      title={t("documents.list")}
      actions={
        <BulkDownload caseId={caseId} disabled={!documents || documents.length === 0} />
      }
    >
      {isLoading ? (
        <Spinner label={t("common.loading")} />
      ) : !documents || documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={t("documents.none")}
          hint={t("documents.noneHint")}
        />
      ) : (
        <Table>
          <THead
            columns={[
              t("documents.type"),
              t("documents.version"),
              t("documents.generatedAt"),
              t("documents.generatedBy"),
              t("common.actions"),
            ]}
          />
          <tbody>
            {documents.map((doc) => (
              <TRow key={doc.id}>
                <TCell className="font-medium text-slate-800">
                  {t(`documents.types.${doc.doc_type}`, doc.doc_type)}
                </TCell>
                <TCell>v{doc.version}</TCell>
                <TCell>{formatDateTime(doc.generated_at)}</TCell>
                <TCell>{doc.generator?.name || t("common.none")}</TCell>
                <TCell>
                  <div className="flex gap-1.5">
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={downloading === `${doc.id}-docx`}
                      onClick={() => download(doc, "docx")}
                    >
                      <FileDown size={13} />
                      DOCX
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={!doc.pdf_path}
                      title={!doc.pdf_path ? t("documents.pdfUnavailable") : undefined}
                      loading={downloading === `${doc.id}-pdf`}
                      onClick={() => download(doc, "pdf")}
                    >
                      <FileDown size={13} />
                      PDF
                    </Button>
                  </div>
                </TCell>
              </TRow>
            ))}
          </tbody>
        </Table>
      )}
    </Card>
  );
}
