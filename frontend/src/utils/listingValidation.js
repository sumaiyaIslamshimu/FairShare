export const CATEGORIES = ["Fashion", "Electronics", "Household", "Groceries"];

// Returns an object keyed by field name; a field is omitted when valid.
export function validateListingForm(values) {
  const errors = {};

  if (!values.name || values.name.trim() === "") {
    errors.name = "Product name is required";
  }

  if (!values.category) {
    errors.category = "Category is required";
  }

  const priceText = String(values.price ?? "").trim();
  if (priceText === "") {
    errors.price = "Price is required";
  } else if (Number.isNaN(Number(priceText)) || Number(priceText) <= 0) {
    errors.price = "Price must be greater than 0";
  }

  const stockText = String(values.stock ?? "").trim();
  if (stockText === "") {
    errors.stock = "Stock is required";
  } else if (!/^\d+$/.test(stockText)) {
    errors.stock = "Stock must be a whole number, 0 or greater";
  }

  return errors;
}

export function getStockStatus(stock) {
  const n = Number(stock);
  if (n === 0) return { label: "Out of stock", className: "bg-red-100 text-red-700" };
  if (n <= 5) return { label: "Low stock", className: "bg-yellow-100 text-yellow-800" };
  return { label: "In stock", className: "bg-green-100 text-green-800" };
}