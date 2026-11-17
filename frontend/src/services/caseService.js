import api from "./api";

export const caseService = {
  async list(params = {}) {
    const { data } = await api.get("/cases", { params });
    return data; // { total, page, page_size, items }
  },

  async search(q) {
    const { data } = await api.get("/cases/search", { params: { q } });
    return data;
  },

  async get(id) {
    const { data } = await api.get(`/cases/${id}`);
    return data;
  },

  async create(payload) {
    const { data } = await api.post("/cases", payload);
    return data;
  },

  async update(id, payload) {
    const { data } = await api.put(`/cases/${id}`, payload);
    return data;
  },

  async remove(id) {
    await api.delete(`/cases/${id}`);
  },

  // ---- persons ----
  async addPerson(caseId, payload) {
    const { data } = await api.post(`/cases/${caseId}/persons`, payload);
    return data;
  },
  async updatePerson(caseId, personId, payload) {
    const { data } = await api.put(
      `/cases/${caseId}/persons/${personId}`,
      payload
    );
    return data;
  },
  async removePerson(caseId, personId) {
    await api.delete(`/cases/${caseId}/persons/${personId}`);
  },

  // ---- seized items ----
  async addItem(caseId, payload) {
    const { data } = await api.post(`/cases/${caseId}/items`, payload);
    return data;
  },
  async updateItem(caseId, itemId, payload) {
    const { data } = await api.put(`/cases/${caseId}/items/${itemId}`, payload);
    return data;
  },
  async removeItem(caseId, itemId) {
    await api.delete(`/cases/${caseId}/items/${itemId}`);
  },

  // ---- legal sections ----
  async addSection(caseId, payload) {
    const { data } = await api.post(`/cases/${caseId}/sections`, payload);
    return data;
  },
  async removeSection(caseId, sectionId) {
    await api.delete(`/cases/${caseId}/sections/${sectionId}`);
  },

  // ---- diary ----
  async diary(caseId) {
    const { data } = await api.get(`/cases/${caseId}/diary`);
    return data;
  },
  async addDiaryEntry(caseId, payload) {
    const { data } = await api.post(`/cases/${caseId}/diary`, payload);
    return data;
  },
};
