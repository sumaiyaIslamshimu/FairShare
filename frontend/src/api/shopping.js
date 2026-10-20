import { request } from "./client.js";

// Only non-empty values go into the query string.
function qs(params = {}) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, v);
  });
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const searchProducts = (params) => request(`/compare/search${qs(params)}`, { auth: false });
export const getGroup = (groupKey) => request(`/compare/groups/${encodeURIComponent(groupKey)}`, { auth: false });
export const getSources = () => request("/compare/sources", { auth: false });
export const getCategories = () => request("/categories", { auth: false });
export const browseSellerProducts = (params) => request(`/seller-products${qs(params)}`, { auth: false });
export const getSellerProduct = (id) => request(`/seller-products/${id}`, { auth: false });