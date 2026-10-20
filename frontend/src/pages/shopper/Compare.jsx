import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import MatchGroupTable from "../../components/shopping/MatchGroupTable.jsx";
import PriceBadge from "../../components/shopping/PriceBadge.jsx";
import { getGroup } from "../../api/shopping.js";
import { describeDifference } from "../../utils/format.js";
import "../../styles/shopping.css";

export default function Compare() {
  const { groupKey } = useParams();
  const [group, setGroup] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getGroup(groupKey)
      .then((g) => !cancelled && setGroup(g))
      .catch((e) => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [groupKey]);

  if (loading) return <Loading />;
  if (error) {
    return (
      <>
        <Link className="back-link" to="/app/search">← Back to search</Link>
        <ErrorBox error={error} />
      </>
    );
  }

  // Show up to 4 offers, always including the cheapest verified one.
  const cheapest = group.exact.find((i) => i.id === group.cheapest_id);
  const rest = group.exact.filter((i) => i.id !== group.cheapest_id);
  const shown = (cheapest ? [cheapest, ...rest] : rest).slice(0, 4);

  return (
    <>
      <Link className="back-link" to="/app/search">← Back to search</Link>
      <h1>Compare prices</h1>
      <p className="subtitle">
        Identical product (same brand, model and size) across {group.exact.length} offers.
        {group.exact.length > shown.length && ` Showing ${shown.length}.`}
        {!group.cheapest_id && " No recently updated, in-stock price is available, so no best price is marked."}
      </p>
      <Card><MatchGroupTable items={shown} cheapestId={group.cheapest_id} /></Card>

      {group.possible.length > 0 && (
        <>
          <h2 style={{ margin: "28px 0 12px" }}>Possible matches (not identical)</h2>
          <Card>
            {group.possible.map(({ item, differences }) => (
              <div className="possible-row" key={`${item.source}-${item.id}`}>
                <div>
                  <strong>{item.name}</strong> <span className="muted">· {item.store_name}</span>
                  <ul className="diff-list">
                    {differences.map((d, idx) => <li key={idx}>{describeDifference(d)}</li>)}
                  </ul>
                </div>
                <PriceBadge item={item} />
              </div>
            ))}
          </Card>
        </>
      )}
    </>
  );
}