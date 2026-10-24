import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { cancelReturn, listMyReturns, requestReturn } from "../../api/returns.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import { REASON_LABEL, RETURN_TONE } from "../../components/ReturnsTable.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate, formatPrice } from "../../utils/format.js";

export default function MyReturns() {
  const [params, setParams] = useSearchParams(); // /app/returns?item=<order item id> opens the request form
  const itemId = params.get("item");
  const { data, error, loading, reload } = useLoad(() => listMyReturns());
  const [form, setForm] = useState({ reason: "damaged", details: "" });
  const [formError, setFormError] = useState(null);
  const [actionError, setActionError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      await requestReturn({ order_item_id: itemId, reason: form.reason, details: form.details });
      setForm({ reason: "damaged", details: "" });
      setParams({});
      reload();
    } catch (err) {
      setFormError(err);
    }
  };

  const cancel = async (r) => {
    setActionError(null);
    try {
      await cancelReturn(r.id);
      reload();
    } catch (err) {
      setActionError(err);
    }
  };

  return (
    <>
      <h1>My returns</h1>
      <p className="subtitle">You can ask to return an item after it has been delivered. The seller decides. Refunds here are simulated; no real money moves.</p>

      {itemId && (
        <Card style={{ marginBottom: 16 }}>
          <h2>Return this item</h2>
          <form onSubmit={submit}>
            <ErrorBox error={formError} />
            <FormField label="Reason" id="ret-reason">
              <select id="ret-reason" className="input" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })}>
                {Object.entries(REASON_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </FormField>
            <FormField label={form.reason === "other" ? "Please explain (at least 10 characters)" : "Details (optional)"} id="ret-details">
              <textarea id="ret-details" className="input" rows={3} maxLength={1000} value={form.details}
                        onChange={(e) => setForm({ ...form, details: e.target.value })} />
            </FormField>
            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="primary" type="submit">Send return request</Button>
              <Button type="button" onClick={() => setParams({})}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          {!data?.items?.length && <p>You have no return requests. Open <strong>My Orders</strong> and choose “Return this item” on a delivered item.</p>}
          {(data?.items || []).map((r) => (
            <Card key={r.id} style={{ marginBottom: 12 }}>
              <h3>{r.quantity}x {r.product_title} <Badge tone={RETURN_TONE[r.status]}>{r.status}</Badge></h3>
              <p>Reason: {REASON_LABEL[r.reason] || r.reason}{r.details ? ` — ${r.details}` : ""}</p>
              <p>Refund if completed: {formatPrice(r.refund_paisa, r.currency)} (simulated)</p>
              {r.seller_note && <p><strong>Seller says:</strong> {r.seller_note}</p>}
              <p className="muted">Asked {formatDate(r.created_at)}</p>
              {r.status === "requested" && <Button onClick={() => cancel(r)}>Cancel request</Button>}
            </Card>
          ))}
        </>
      )}
    </>
  );
}