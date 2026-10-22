import { request } from "./client.js";

function qs(params = {}) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, v);
  });
  const s = p.toString();
  return s ? `?${s}` : "";
}

// Public Listings
export const browseRentals = (params) => request(`/rentals/listings${qs(params)}`, { auth: false });
export const getRentalListing = (id) => request(`/rentals/listings/${id}`, { auth: false });

// Owner Listing Management
export const getMyListings = (page = 1) => request(`/rentals/my/listings?page=${page}`);
export const createListing = (data) => request("/rentals/listings", { method: "POST", body: data });
export const updateListing = (id, data) => request(`/rentals/listings/${id}`, { method: "PUT", body: data });
export const deleteListing = (id) => request(`/rentals/listings/${id}`, { method: "DELETE" });

// Renter Requests
export const submitRequest = (data) => request("/rentals/requests", { method: "POST", body: data });
export const getMyRequests = (page = 1) => request(`/rentals/my/requests?page=${page}`);
export const cancelRequest = (id) => request(`/rentals/requests/${id}/cancel`, { method: "POST" });

// Owner Request Management
export const getIncomingRequests = (page = 1) => request(`/rentals/incoming-requests?page=${page}`);
export const decideRequest = (id, action) => request(`/rentals/requests/${id}/decision`, { method: "POST", body: { action } });

// Shared (Bookings & Events)
export const getMyBookings = (page = 1) => request(`/rentals/bookings?page=${page}`);
export const getRentalEvents = (id) => request(`/rentals/requests/${id}/events`);