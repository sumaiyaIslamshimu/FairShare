import { request, requestBlob } from "./client.js";

const qs = (params = {}) => {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") q.set(k, v);
  });
  const text = q.toString();
  return text ? `?${text}` : "";
};

export const getStats = () => request("/admin/stats");

export const listUsers = (params) => request(`/admin/users${qs(params)}`);
export const setUserActive = (id, is_active) => request(`/admin/users/${id}`, { method: "PATCH", body: { is_active } });

export const listSellers = (params) => request(`/admin/sellers${qs(params)}`);
export const setSellerStatus = (id, status) => request(`/admin/sellers/${id}`, { method: "PATCH", body: { status } });

export const listVerifications = (params) => request(`/admin/verifications${qs(params)}`);
export const decideVerification = (id, decision, note) =>
  request(`/admin/verifications/${id}`, { method: "PATCH", body: { decision, note } });
export const fetchVerificationDocument = (id) => requestBlob(`/admin/verifications/${id}/document`);

export const listAdminProducts = (params) => request(`/admin/products${qs(params)}`);
export const moderateProduct = (id, moderation_status) =>
  request(`/admin/products/${id}`, { method: "PATCH", body: { moderation_status } });
export const listAdminRentals = (params) => request(`/admin/rentals${qs(params)}`);
export const moderateRental = (id, status) => request(`/admin/rentals/${id}`, { method: "PATCH", body: { status } });

export const listTaxonomy = () => request("/admin/categories");
export const createCategory = (body) => request("/admin/categories", { method: "POST", body });
export const updateCategory = (slug, body) => request(`/admin/categories/${slug}`, { method: "PUT", body });
export const deleteCategory = (slug) => request(`/admin/categories/${slug}`, { method: "DELETE" });
export const createSubcategory = (body) => request("/admin/subcategories", { method: "POST", body });
export const updateSubcategory = (slug, body) => request(`/admin/subcategories/${slug}`, { method: "PUT", body });
export const deleteSubcategory = (slug) => request(`/admin/subcategories/${slug}`, { method: "DELETE" });

export const listAdminComplaints = (params) => request(`/admin/complaints${qs(params)}`);
export const updateComplaint = (id, body) => request(`/admin/complaints/${id}`, { method: "PATCH", body });

export const getScrapingStatus = () => request("/admin/scraping/status");
export const getScrapingRuns = (params) => request(`/admin/scraping/runs${qs(params)}`);
export const refreshStore = (store) => request(`/admin/scraping/refresh/${store}`, { method: "POST" });

export const listAudit = (params) => request(`/admin/audit${qs(params)}`);


export const listAdminReviews = (params) => request(`/admin/reviews${qs(params)}`);
export const moderateReview = (id, status) => request(`/admin/reviews/${id}`, { method: "PATCH", body: { status } });

export const listAdminReturns = (params) => request(`/admin/returns${qs(params)}`);
export const decideAdminReturn = (id, action, note = "") =>
  request(`/admin/returns/${id}`, { method: "PATCH", body: { action, note } });