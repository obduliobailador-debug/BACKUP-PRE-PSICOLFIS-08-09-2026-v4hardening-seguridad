import axios from "axios";
import { API } from "../../api";

export const useAdminApi = (token, onAuthFail) => ({
  get: async (path) => {
    try {
      const { data } = await axios.get(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
      return data;
    } catch (err) {
      if (err?.response?.status === 401 || err?.response?.status === 403) onAuthFail?.();
      throw err;
    }
  },
  post: async (path, body) => {
    const { data } = await axios.post(`${API}${path}`, body, { headers: { Authorization: `Bearer ${token}` } });
    return data;
  },
  patch: async (path, body) => {
    const { data } = await axios.patch(`${API}${path}`, body, { headers: { Authorization: `Bearer ${token}` } });
    return data;
  },
  del: async (path) => {
    const { data } = await axios.delete(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
    return data;
  },
});
