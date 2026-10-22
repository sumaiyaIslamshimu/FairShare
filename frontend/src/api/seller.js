import { request } from "./client.js";

// Profile & Insights
export const getSellerProfile = () => request("/seller/profile");
export const updateSellerProfile = (data) => request("/seller/profile", { method: "PUT", body: data });
export const getSellerInsights = () => request("/seller/insights");

// Promotions
export const getPromotions = () => request("/seller/promotions");
export const createPromotion = (data) => request("/seller/promotions", { method: "POST", body: data });
export const updatePromotion = (id, data) => request(`/seller/promotions/${id}`, { method: "PUT", body: data });
export const deletePromotion = (id) => request(`/seller/promotions/${id}`, { method: "DELETE" });

// Seller Products (Owner management - M2 built backend, M3 builds UI)
export const getMyProducts = (page = 1) => request(`/seller/products?page=${page}`);
export const createProduct = (data) => request("/seller/products", { method: "POST", body: data });
export const updateProduct = (id, data) => request(`/seller/products/${id}`, { method: "PUT", body: data });
export const deleteProduct = (id) => request(`/seller/products/${id}`, { method: "DELETE" });
export const updateInventory = (id, qty) => request(`/seller/products/${id}/inventory`, { method: "PATCH", body: { stock_qty: qty } });

// Seller Orders
export const getSellerOrders = (page = 1) => request(`/seller/orders?page=${page}`);
export const updateOrderStatus = (id, status) => request(`/seller/orders/${id}/status`, { method: "PATCH", body: { status } });