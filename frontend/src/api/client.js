// The ONE place that talks to the backend. Adds the JWT and normalizes errors.
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const TOKEN_KEY = "fairshare_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(message, status = 0, code = "ERROR", details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { Accept: "application/json" };
  // FormData (file uploads): the browser sets the multipart Content-Type and boundary itself.
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  const token = tokenStore.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the backend is running.", 0, "NETWORK_ERROR");
  }

  let data = null;
  if (res.status !== 204) {
    try {
      data = await res.json();
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    if (res.status === 401 && auth) tokenStore.clear();
    const err = data && data.error ? data.error : {};
    throw new ApiError(err.message || `Request failed (${res.status}).`, res.status, err.code || "ERROR", err.details || null);
  }
  return data;
}

// Authenticated download (e.g. an admin viewing a private document). Returns a Blob.
export async function requestBlob(path) {
  const token = tokenStore.get();
  let res;
  try {
    res = await fetch(`${BASE}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the backend is running.", 0, "NETWORK_ERROR");
  }
  if (!res.ok) {
    let err = {};
    try {
      err = (await res.json()).error || {};
    } catch {
      err = {};
    }
    throw new ApiError(err.message || `Request failed (${res.status}).`, res.status, err.code || "ERROR");
  }
  return res.blob();
}