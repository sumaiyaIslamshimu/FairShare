import { request } from "./client.js";

export const createReview = (body) => request("/reviews", { method: "POST", body });
export const updateReview = (id, body) => request(`/reviews/${id}`, { method: "PUT", body });
export const deleteReview = (id) => request(`/reviews/${id}`, { method: "DELETE" });
export const listMyReviews = (page = 1) => request(`/reviews/mine?page=${page}`);
export const listProductReviews = (productId, page = 1) =>
  request(`/seller-products/${productId}/reviews?page=${page}`, { auth: false });
export const listSellerReviews = (page = 1) => request(`/seller/reviews?page=${page}`);