import api from "./api";

export const authService = {
  async login(badgeNo, password) {
    const { data } = await api.post("/auth/login", {
      badge_no: badgeNo,
      password,
    });
    return data; // { access_token, refresh_token, token_type, user }
  },

  async me() {
    const { data } = await api.get("/auth/me");
    return data;
  },

  async logout() {
    try {
      await api.post("/auth/logout");
    } catch {
      // stateless logout — ignore network errors
    }
  },
};
