// All seller-listing API calls live here. Endpoint paths and field names are
// defined once so they are easy to change when the backend task is finished.

import { getToken } from "../utils/sellerAuth";

const API_BASE_URL = "http://localhost:8000";

// Set to false once [Backend] 1.2 Build the seller listings API is ready.
const USE_MOCK_API = true;

const ENDPOINTS = {
  list: "/seller/listings",
  create: "/seller/listings",
  update: (id) => `/seller/listings/${id}`,
  remove: (id) => `/seller/listings/${id}`,
};

// ---------- Mock store (only used when USE_MOCK_API is true) ----------
let mockListings = [
  {
    id: "mock-1",
    name: "Lotto BLACK SUPERLIGHT Shoes (Size 44)",
    brand: "Lotto",
    category: "Fashion",
    price: 2100,
    stock: 10,
    description: "Lightweight everyday shoes.",
    image_link: "",
  },
  {
    id: "mock-2",
    name: "Bata Formal Slip-on Sandals",
    brand: "Bata",
    category: "Fashion",
    price: 1450,
    stock: 3,
    description: "Formal slip-on sandals.",
    image_link: "",
  },
  {
    id: "mock-3",
    name: "Miyako Electric Kettle 1.5L",
    brand: "Miyako",
    category: "Household",
    price: 1250,
    stock: 0,
    description: "1.5 litre electric kettle.",
    image_link: "",
  },
];

// ---------- Helpers ----------
function normalizeListing(raw) {
  return { ...raw, id: raw.id || raw._id };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...(options.headers || {}),
    },
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      "Something went wrong. Please try again.";
    throw new Error(typeof message === "string" ? message : "Something went wrong. Please try again.");
  }

  return data;
}

// ---------- Public API ----------
export async function getSellerListings() {
  if (USE_MOCK_API) return mockListings.map(normalizeListing);
  const data = await request(ENDPOINTS.list);
  return (data || []).map(normalizeListing);
}

export async function createSellerListing(payload) {
  if (USE_MOCK_API) {
    const created = { ...payload, id: `mock-${Date.now()}` };
    mockListings = [created, ...mockListings];
    return created;
  }
  const data = await request(ENDPOINTS.create, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return normalizeListing(data);
}

export async function updateSellerListing(id, payload) {
  if (USE_MOCK_API) {
    mockListings = mockListings.map((l) => (l.id === id ? { ...l, ...payload } : l));
    return mockListings.find((l) => l.id === id);
  }
  const data = await request(ENDPOINTS.update(id), {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  return normalizeListing(data);
}

export async function deleteSellerListing(id) {
  if (USE_MOCK_API) {
    mockListings = mockListings.filter((l) => l.id !== id);
    return true;
  }
  await request(ENDPOINTS.remove(id), { method: "DELETE" });
  return true;
}