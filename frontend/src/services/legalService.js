import api from "./api";

export const legalService = {
  async suggest(narrative, language = "en") {
    const { data } = await api.post("/legal/suggest", { narrative, language });
    return data; // { sections, judgments, entities }
  },

  async search(q, act = "") {
    const params = { q };
    if (act) params.act = act;
    const { data } = await api.get("/legal/search", { params });
    return data;
  },

  async section(act, number) {
    const { data } = await api.get(`/legal/section/${act}/${number}`);
    return data;
  },
};
