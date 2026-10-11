// Frontend-only seller session check. This only controls what the UI shows;
// real authorization MUST be enforced by the backend.

export const TOKEN_KEY = "access_token";
export const SELLER_ROLE = "seller"; // change if your backend uses another role value

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function decodeTokenPayload(token) {
  try {
    const part = token.split(".")[1];
    let base64 = part.replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4) base64 += "=";
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

// Returns { token, userId } for a valid, unexpired seller token, otherwise null.
export function getSellerSession() {
  const token = getToken();
  if (!token) return null;

  const payload = decodeTokenPayload(token);
  if (!payload) return null;
  if (payload.exp && payload.exp * 1000 < Date.now()) return null;
  if (payload.role !== SELLER_ROLE) return null;

  return { token, userId: payload.sub };
}