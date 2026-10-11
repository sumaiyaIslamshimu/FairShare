

const API_BASE_URL = "http://127.0.0.1:8000";

async function parseJsonSafely(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}


export async function getProductComparison(productId) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/compare`);

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Product not found");
    }
    const message =
      (data && (data.detail || data.message)) ||
      "Failed to load product comparison. Please try again.";
    throw new Error(
      typeof message === "string"
        ? message
        : "Failed to load product comparison. Please try again."
    );
  }

  return data;
}


export async function getProductRanking(productId) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/ranking`);

  const data = await parseJsonSafely(response);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Product not found");
    }
    const message =
      (data && (data.detail || data.message)) ||
      "Failed to load best-value ranking. Please try again.";
    throw new Error(
      typeof message === "string"
        ? message
        : "Failed to load best-value ranking. Please try again."
    );
  }

  return data;
}