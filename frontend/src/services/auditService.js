import api from "./api";

export const auditService = {
  async query(params = {}) {
    // Strip empty filters so the API sees only real ones
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== "" && v != null)
    );
    const { data } = await api.get("/audit", { params: clean });
    return data;
  },
};
