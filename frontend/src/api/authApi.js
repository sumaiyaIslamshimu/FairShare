// Centralizes all calls to the FastAPI auth backend.
// Pages should never call fetch() directly — always go through here.

const API_BASE_URL = "http://127.0.0.1:8000";

async function parseJsonSafely(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/**
 * Registers a new shopper.
 * Sends only name, email, phone, password — confirmPassword and the
 * terms checkbox are frontend-only and never sent to the backend.
 *
 * Returns the parsed UserOut JSON on success.
 * Throws an Error with a user-facing message on failure.
 */
export async function registerUser({ name, email, phone, password }) {
  const response = await fetch(`${API_BASE_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, phone, password }),
  });

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      "Registration failed. Please try again.";
    throw new Error(typeof message === "string" ? message : "Registration failed. Please try again.");
  }

  return data;
}

/**
 * Logs in a shopper.
 * The Figma "Email or Username" field's value is always submitted
 * as `email` — the backend only supports email + password.
 *
 * Returns the parsed TokenResponse JSON ({ access_token, token_type, user }).
 * Throws an Error with a user-facing message on failure.
 */
export async function loginUser({ email, password }) {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      "Login failed. Please try again.";
    throw new Error(typeof message === "string" ? message : "Login failed. Please try again.");
  }

  return data;
}