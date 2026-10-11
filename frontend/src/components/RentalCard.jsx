import "./RentalCard.css";

const CURRENCY = "$";

const CATEGORY_EMOJI = {
  Electronics: "💻",
  Household: "🏠",
  Fashion: "🎒",
  Groceries: "🛒",
};

function RentalCard({ item }) {
  const emoji = item.emoji || CATEGORY_EMOJI[item.category] || "📦";

  return (
    <div className="rental-card">
      <div className="rental-card-image">
        {!item.is_available && (
          <span className="unavailable-tag">Unavailable</span>
        )}
        <span className="rental-emoji">{emoji}</span>
      </div>

      <div className="rental-card-body">
        <div className="rental-card-name">{item.name}</div>
        <div className="rental-card-location">📍 {item.location}</div>

        <div className="rental-card-price">
          {CURRENCY}{item.price_per_day}
          <span className="rental-card-unit">/day</span>
        </div>

        <button
          className="btn-primary rental-card-btn"
          disabled={!item.is_available}
        >
          {item.is_available ? "View & Request" : "Unavailable"}
        </button>
      </div>
    </div>
  );
}

export default RentalCard;