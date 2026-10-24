import { Link } from "react-router-dom";
import Badge from "../Badge.jsx";
import Card from "../Card.jsx";
import { formatSize } from "../../utils/format.js";
import FreshnessBadge from "./FreshnessBadge.jsx";
import PriceBadge from "./PriceBadge.jsx";
import StoreLink from "./StoreLink.jsx";
import TrackButton from "./TrackButton.jsx";

const AVAILABILITY = {
  in_stock: ["green", "In Stock"],
  out_of_stock: ["red", "Out of stock"],
  unknown: ["neutral", "Availability unknown"],
};

export default function ProductCard({ item }) {
  const isExternal = item.source === "external";
  const [tone, label] = AVAILABILITY[item.availability] || AVAILABILITY.unknown;
  const size = formatSize(item.quantity, item.unit);
  return (
    <Card className="product-card">
      {item.image_url ? (
        <img src={item.image_url} alt={item.name} loading="lazy" />
      ) : (
        <div className="product-thumb">{item.name.charAt(0)}</div>
      )}
      <div className="badge-row">
        <Badge tone={isExternal ? "neutral" : "green"}>{item.store_name}</Badge>
        <Badge tone={tone}>{label}</Badge>
      </div>
      {isExternal ? <strong>{item.name}</strong> : <Link to={`/app/product/${item.id}`}><strong>{item.name}</strong></Link>}
      {item.brand && <span className="muted">{item.brand}</span>}
      {size && <span className="muted">Size: {size}</span>}
      <PriceBadge item={item} />
      <FreshnessBadge freshness={item.freshness} source={item.source} />
      {isExternal ? (
        <StoreLink url={item.store_url}>View at {item.store_name}</StoreLink>
      ) : (
        <span className="muted">Sold on FairShare{item.seller_name ? ` by ${item.seller_name}` : ""}</span>
      )}
      <TrackButton item={item} />
      {item.group_key && item.group_size >= 2 && (
        <Link className="btn" to={`/app/compare/${item.group_key}`}>
          Compare prices ({item.group_size})
        </Link>
      )}
    </Card>
  );
}