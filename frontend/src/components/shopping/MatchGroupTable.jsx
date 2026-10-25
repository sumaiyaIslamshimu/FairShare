import Badge from "../Badge.jsx";
import { formatDate, formatSize } from "../../utils/format.js";
import FreshnessBadge from "./FreshnessBadge.jsx";
import PriceBadge from "./PriceBadge.jsx";
import StoreLink from "./StoreLink.jsx";
import TrackButton from "./TrackButton.jsx";
import useTrackedRefs from "../../hooks/useTrackedRefs.js";

const AVAILABILITY = { in_stock: "In Stock", out_of_stock: "Out of stock" };

// Side-by-side table. Missing values show "Not available" and are never invented.
export default function MatchGroupTable({ items, cheapestId }) {
  const { isTracked } = useTrackedRefs();

  const rows = [
    ["Price", (i) => (
      <>
        <PriceBadge item={i} />
        {i.id === cheapestId && <Badge tone="green">Best price</Badge>}
      </>
    )],
    ["Availability", (i) => AVAILABILITY[i.availability] || "Not available"],
    ["Package size", (i) => formatSize(i.quantity, i.unit) || "Not available"],
    ["Data status", (i) => <FreshnessBadge freshness={i.freshness} source={i.source} />],
    ["Last updated", (i) => formatDate(i.last_updated)],
    ["Price alert", (i) => <TrackButton item={i} tracked={isTracked(i)} />],
    ["Link", (i) => (i.source === "external" ? <StoreLink url={i.store_url}>Open store page</StoreLink> : "Sold on FairShare")],
  ];
  return (
    <div className="table-wrap">
      <table className="table compare-table">
        <thead>
          <tr>
            <th />
            {items.map((i) => (
              <th key={i.id}>
                {i.store_name}
                <div className="muted" style={{ textTransform: "none", letterSpacing: 0 }}>{i.name}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, render]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              {items.map((i) => (
                <td key={i.id} className={label === "Price" && i.id === cheapestId ? "best-cell" : ""}>
                  {render(i)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}