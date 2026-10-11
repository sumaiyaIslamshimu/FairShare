

import { getToken } from "../utils/sellerAuth";

const API_BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = data && (data.detail || data.message);
    let message = "Something went wrong. Please try again.";
    if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail) && detail[0] && detail[0].msg) {
      message = detail[0].msg;
    }
    throw new Error(message);
  }

  return data;
}

function sellerHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  };
}

export function getListingDiscount(listingId) {
  return request(`/promotions/listings/${listingId}/discount`);
}

export function saveListingDiscount(listingId, payload) {
  return request(`/promotions/listings/${listingId}/discount`, {
    method: "PUT",
    headers: sellerHeaders(),
    body: JSON.stringify(payload),
  });
}

export function removeListingDiscount(listingId) {
  return request(`/promotions/listings/${listingId}/discount`, {
    method: "DELETE",
    headers: sellerHeaders(),
  });
}

// Returns { [listingId]: { percentage, original_price, discounted_price, ends_at } }
// containing only discounts that are active right now.
export async function getActiveDiscounts(listingIds) {
  const ids = (listingIds || []).filter(Boolean);
  if (ids.length === 0) return {};
  const data = await request(
    `/promotions/active?ids=${encodeURIComponent(ids.join(","))}`
  );
  return (data && data.discounts) || {};
}

export function getSpotlightSellers() {
  return request("/promotions/spotlight");
}