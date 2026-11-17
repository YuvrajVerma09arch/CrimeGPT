import api, { saveBlob } from "./api";

export const DOC_TYPES = [
  "CHARGESHEET",
  "MEDICAL_LETTER",
  "REMAND_REQUEST",
  "SEIZURE_RECEIPT",
  "COURT_CUSTODY",
  "PANCHANAMA",
  "FACE_ID_FORM",
];

export const documentService = {
  async list(caseId) {
    const { data } = await api.get(`/cases/${caseId}/documents`);
    return data;
  },

  async generate(caseId, docTypes) {
    const { data } = await api.post(`/cases/${caseId}/documents/generate`, {
      doc_types: docTypes,
    });
    return data; // { task_id, status, documents }
  },

  async download(doc, format = "docx") {
    const res = await api.get(`/documents/${doc.id}/download`, {
      params: { format },
      responseType: "blob",
    });
    saveBlob(res.data, `${doc.doc_type}_v${doc.version}.${format}`);
  },

  async bulkDownload(caseId) {
    const res = await api.post(
      `/cases/${caseId}/documents/bulk-download`,
      null,
      { responseType: "blob" }
    );
    saveBlob(res.data, "fir_documents.zip");
  },
};
