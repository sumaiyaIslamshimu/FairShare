import "./RentalFilterBar.css";

const CATEGORIES = [
  "Electronics",
  "Household",
  "Fashion",
  "Groceries",
];

function RentalFilterBar({ filters, onChange }) {
  const update = (field, value) => {
    onChange({ ...filters, [field]: value });
  };

  return (
    <div className="rental-filter-bar">
      <div className="rental-search">
        <span>🔍</span>

        <input
          type="text"
          placeholder="Search rental items..."
          value={filters.q}
          onChange={(e) => update("q", e.target.value)}
        />
      </div>

      <select
        value={filters.category}
        onChange={(e) => update("category", e.target.value)}
      >
        <option value="">All Categories</option>

        {CATEGORIES.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <input
        className="rental-max-price"
        type="number"
        min="0"
        placeholder="Max price/day"
        value={filters.maxPrice}
        onChange={(e) => update("maxPrice", e.target.value)}
      />
    </div>
  );
}

export default RentalFilterBar;