import { request } from "./client.js";

export const requestReturn = (body) => request("/returns", { method: "POST", body });
export const listMyReturns = (page = 1) => request(`/returns/mine?page=${page}`);
export const cancelReturn = (id) => request(`/returns/${id}/cancel`, { method: "POST" });
export function listSellerReturns(params = {}) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v && q.set(k, v));
  const text = q.toString();
  const suffix = text ? "?" + text : "";
  return request(`/seller/returns${suffix}`);
}
export const decideSellerReturn = (id, action, note = "") =>
  request(`/seller/returns/${id}`, { method: "PATCH", body: { action, note } });