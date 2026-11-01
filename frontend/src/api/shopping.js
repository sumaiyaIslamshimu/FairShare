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
export const placeDirectOrder = (data) => request("/orders/place", { method: "POST", data });
export const processCheckout = (data) => request("/checkout", { method: "POST", data });
// frontend/src/api/shopping.js
export const getCart = () => request("/cart");
export const addToCart = (data) => request("/cart/items", { method: "POST", data });
export const updateCartItem = (itemId, data) => request(`/cart/items/${itemId}`, { method: "PATCH", data });
export const removeCartItem = (itemId) => request(`/cart/items/${itemId}`, { method: "DELETE" });
