import { request } from "./client.js";

// Cart
export const getCart = () => request("/cart");
export const addToCart = (productId, quantity = 1) => request("/cart/items", { method: "POST", body: { seller_product_id: productId, quantity } });
export const updateCartItem = (productId, quantity) => request(`/cart/items/${productId}`, { method: "PUT", body: { quantity } });
export const removeCartItem = (productId) => request(`/cart/items/${productId}`, { method: "DELETE" });
export const clearCart = () => request("/cart", { method: "DELETE" });

// Checkout & Shopper Orders
export const checkout = (data) => request("/checkout", { method: "POST", body: data });
export const getMyOrders = (page = 1) => request(`/orders?page=${page}`);
export const cancelOrder = (id) => request(`/orders/${id}/cancel`, { method: "POST" });