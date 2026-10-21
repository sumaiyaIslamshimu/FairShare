// Display helpers. Money arrives as integer paisa (BDT x 100); missing data is shown as "Not available", never invented.
export function formatPrice(paisa, currency) {
  if (paisa === null || paisa === undefined) return "Not available";
  const amount = (paisa / 100).toLocaleString("en-BD", {
    minimumFractionDigits: paisa % 100 ? 2 : 0,
    maximumFractionDigits: 2,
  });
  return currency === "BDT" ? `৳ ${amount}` : `${amount} (currency not stated)`;
}

export function formatSize(quantity, unit) {
  if (quantity === null || quantity === undefined || !unit) return null;
  if (unit === "g" && quantity >= 1000) return `${quantity / 1000} kg`;
  if (unit === "ml" && quantity >= 1000) return `${quantity / 1000} L`;
  return `${quantity} ${unit}`;
}

export function formatDate(iso) {
  if (!iso) return "Not available";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "Not available" : d.toLocaleString();
}

const FIELD_LABELS = {
  package_size: "Package size",
  brand: "Brand",
  model_or_variant: "Model / variant",
  name_words: "Product name",
};

const show = (v) => (Array.isArray(v) ? (v.length ? v.join(", ") : "—") : v ?? "not stated");

export function describeDifference(d) {
  return `${FIELD_LABELS[d.field] || d.field}: ${show(d.a)} vs ${show(d.b)}`;
}