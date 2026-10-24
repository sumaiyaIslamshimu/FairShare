import { request } from "./client.js";

export const addWatch = (body) => request("/watches", { method: "POST", body });
export const listWatchRefs = () => request("/watches/refs");
export const listWatches = (page = 1) => request(`/watches?page=${page}`);
export const setWatchTarget = (id, target_price_paisa) =>
  request(`/watches/${id}`, { method: "PATCH", body: { target_price_paisa } });
export const removeWatch = (id) => request(`/watches/${id}`, { method: "DELETE" });
export const getWatchHistory = (id) => request(`/watches/${id}/history`);