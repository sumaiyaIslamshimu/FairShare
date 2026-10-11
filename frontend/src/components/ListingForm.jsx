import { useState } from "react";
import { CATEGORIES, validateListingForm } from "../../utils/listingValidation";

const EMPTY_VALUES = {
  name: "",
  brand: "",
  category: "",
  price: "",
  stock: "",
  description: "",
  image_link: "",
};

// One form for both Add (initialValues omitted) and Edit (initialValues provided).
export default function ListingForm({
  initialValues,
  onSubmit,
  onCancel,
  isSubmitting,
  serverError,
}) {
  const [values, setValues] = useState({ ...EMPTY_VALUES, ...(initialValues || {}) });
  const [errors, setErrors] = useState({});

  function handleChange(field, value) {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();

    const validationErrors = validateListingForm(values);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length > 0) {
      return; // invalid data is never sent to the backend
    }

    onSubmit({
      name: values.name.trim(),
      brand: values.brand.trim(),
      category: values.category,
      price: Number(values.price),
      stock: Number(values.stock),
      description: values.description.trim(),
      image_link: values.image_link.trim(),
    });
  }

  const inputClass = (field) =>
    `w-full border rounded-lg px-4 py-2 text-sm ${
      errors[field] ? "border-red-500" : "border-gray-300"
    }`;

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 space-y-5"
    >
      {serverError && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm">
          {serverError}
        </div>
      )}

      <div>
        <label htmlFor="name" className="block text-sm font-semibold text-gray-900 mb-1">
          Product name
        </label>
        <input
          id="name"
          type="text"
          value={values.name}
          onChange={(e) => handleChange("name", e.target.value)}
          className={inputClass("name")}
        />
        {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
      </div>

      <div>
        <label htmlFor="brand" className="block text-sm font-semibold text-gray-900 mb-1">
          Brand
        </label>
        <input
          id="brand"
          type="text"
          value={values.brand}
          onChange={(e) => handleChange("brand", e.target.value)}
          className={inputClass("brand")}
        />
      </div>

      <div>
        <label htmlFor="category" className="block text-sm font-semibold text-gray-900 mb-1">
          Category
        </label>
        <select
          id="category"
          value={values.category}
          onChange={(e) => handleChange("category", e.target.value)}
          className={inputClass("category")}
        >
          <option value="">Select a category</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        {errors.category && <p className="text-red-500 text-xs mt-1">{errors.category}</p>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label htmlFor="price" className="block text-sm font-semibold text-gray-900 mb-1">
            Price (৳)
          </label>
          <input
            id="price"
            type="number"
            step="any"
            value={values.price}
            onChange={(e) => handleChange("price", e.target.value)}
            className={inputClass("price")}
          />
          {errors.price && <p className="text-red-500 text-xs mt-1">{errors.price}</p>}
        </div>

        <div>
          <label htmlFor="stock" className="block text-sm font-semibold text-gray-900 mb-1">
            Stock quantity
          </label>
          <input
            id="stock"
            type="number"
            value={values.stock}
            onChange={(e) => handleChange("stock", e.target.value)}
            className={inputClass("stock")}
          />
          {errors.stock && <p className="text-red-500 text-xs mt-1">{errors.stock}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-semibold text-gray-900 mb-1">
          Description
        </label>
        <textarea
          id="description"
          rows={4}
          value={values.description}
          onChange={(e) => handleChange("description", e.target.value)}
          className={inputClass("description")}
        />
      </div>

      <div>
        <label htmlFor="image_link" className="block text-sm font-semibold text-gray-900 mb-1">
          Image link
        </label>
        <input
          id="image_link"
          type="text"
          value={values.image_link}
          onChange={(e) => handleChange("image_link", e.target.value)}
          className={inputClass("image_link")}
        />
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-5 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-60"
        >
          {isSubmitting ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-5 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}