import { useState } from "react";
import { getWatchHistory, listWatches, removeWatch, setWatchTarget } from "../../api/watches.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate, formatPrice } from "../../utils/format.js";

const PAGE_SIZE = 20;
const STATUS = {
  target_reached: ["green", "Target reached"],
  dropped: ["green", "Cheaper than when you started"],
  unchanged: ["neutral", "Same price"],
  increased: ["amber", "More expensive"],
  unavailable: ["red", "No longer available"],
};

export default function PriceWatch() {
  const [page, setPage] = useState(1);
  const { data, error, loading, reload } = useLoad(() => listWatches(page), [page]);
  const [actionError, setActionError] = useState(null);
  const [history, setHistory] = useState({}); // watch id -> history response

  const act = async (fn) => {
    setActionError(null);
    try {
      await fn();
      reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const editTarget = (w) => {
    const answer = window.prompt("Alert me at or below (Taka). Leave empty to be told about any drop.",
      w.target_price_paisa ? String(w.target_price_paisa / 100) : "");
    if (answer === null) return;
    const text = answer.trim();
    const taka = Number(text);
    if (text && !(taka > 0)) return setActionError(new Error("Enter a number above 0."));
    act(() => setWatchTarget(w.id, text ? Math.round(taka * 100) : null));
  };

  const toggleHistory = async (w) => {
    if (history[w.id]) return setHistory({ ...history, [w.id]: null });
    setActionError(null);
    try {
      setHistory({ ...history, [w.id]: await getWatchHistory(w.id) });
    } catch (e) {
      setActionError(e);
    }
  };

  return (
    <>
      <h1>Price watch</h1>
      <p className="subtitle">
        Products you are tracking. You get a notification when a price drops. Prices come from the store listings we last read and may be out of date; check the store before buying.
      </p>
      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          {!data?.items?.length && <p>You are not tracking anything yet. On a product or a comparison page, choose “Track price”.</p>}
          {(data?.items || []).map((w) => {
            const [tone, label] = STATUS[w.status] || STATUS.unchanged;
            const h = history[w.id];
            return (
              <Card key={w.id} style={{ marginBottom: 12 }}>
                <h3>{w.name || "Product"} <Badge tone={tone}>{label}</Badge></h3>
                <p className="muted">{w.store_name}{w.freshness === "stale" ? " · price may be out of date" : ""}</p>
                <p>
                  Now: <strong>{w.current_price_paisa == null ? "Not available" : formatPrice(w.current_price_paisa, w.currency)}</strong>
                  {" · "}When you started: {formatPrice(w.price_when_added_paisa, w.currency)}
                  {w.lowest_seen_paisa != null && <> · Lowest seen: {formatPrice(w.lowest_seen_paisa, w.currency)}</>}
                  {w.target_price_paisa != null && <> · Your target: {formatPrice(w.target_price_paisa, w.currency)}</>}
                </p>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {w.store_url && <a className="btn" href={w.store_url} target="_blank" rel="noopener noreferrer">Open store page</a>}
                  <Button onClick={() => editTarget(w)}>Change target</Button>
                  <Button onClick={() => toggleHistory(w)}>{h ? "Hide history" : "Price history"}</Button>
                  <Button onClick={() => act(() => removeWatch(w.id))}>Stop tracking</Button>
                </div>
                {h && (
                  h.available && h.points.length ? (
                    <ul style={{ marginTop: 8 }}>
                      {h.points.map((p, i) => <li key={i}>{formatDate(p.observed_at)}: {formatPrice(p.price_paisa, w.currency)}</li>)}
                    </ul>
                  ) : (
                    <p className="muted">No price history is stored for this product. Only the price when you started tracking is known.</p>
                  )
                )}
              </Card>
            );
          })}
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
    </>
  );
}