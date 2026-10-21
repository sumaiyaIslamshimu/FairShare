import { formatPrice } from "../../utils/format.js";

export default function PriceBadge({ item }) {
  return (
    <div>
      <span className="price">{formatPrice(item.price_paisa, item.currency)}</span>
      {item.original_price_paisa ? (
        <span className="price-old">{formatPrice(item.original_price_paisa, item.currency)}</span>
      ) : null}
      {item.discount_percent ? (
        <span className="badge badge-red" style={{ marginLeft: 6 }}>-{Math.round(item.discount_percent)}%</span>
      ) : null}
    </div>
  );
}