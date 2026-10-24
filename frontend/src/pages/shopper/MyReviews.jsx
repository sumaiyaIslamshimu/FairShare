import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { createReview, deleteReview, listMyReviews, updateReview } from "../../api/reviews.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import Stars from "../../components/Stars.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

export default function MyReviews() {
  const [params, setParams] = useSearchParams(); // /app/reviews?item=<order item id> opens the "write" form
  const itemId = params.get("item");
  const { data, error, loading, reload } = useLoad(() => listMyReviews());
  const [form, setForm] = useState({ rating: "5", comment: "" });
  const [editing, setEditing] = useState(null);
  const [formError, setFormError] = useState(null);
  const [actionError, setActionError] = useState(null);

  const submitNew = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      await createReview({ order_item_id: itemId, rating: Number(form.rating), comment: form.comment });
      setForm({ rating: "5", comment: "" });
      setParams({});
      reload();
    } catch (err) {
      setFormError(err);
    }
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      await updateReview(editing.id, { rating: Number(editing.rating), comment: editing.comment });
      setEditing(null);
      reload();
    } catch (err) {
      setFormError(err);
    }
  };

  const remove = async (r) => {
    if (!window.confirm("Delete this review?")) return;
    setActionError(null);
    try {
      await deleteReview(r.id);
      reload();
    } catch (err) {
      setActionError(err);
    }
  };

  const ratingSelect = (value, onChange, id) => (
    <FormField label="Rating" id={id}>
      <select id={id} className="input" value={value} onChange={onChange}>
        {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} out of 5</option>)}
      </select>
    </FormField>
  );

  return (
    <>
      <h1>My reviews</h1>
      <p className="subtitle">You can review an item once it has been delivered. Other shoppers see your first name and your review.</p>

      {itemId && (
        <Card style={{ marginBottom: 16 }}>
          <h2>Write a review</h2>
          <form onSubmit={submitNew}>
            <ErrorBox error={formError} />
            {ratingSelect(form.rating, (e) => setForm({ ...form, rating: e.target.value }), "rv-rating")}
            <FormField label="Your comment (optional)" id="rv-comment">
              <textarea id="rv-comment" className="input" rows={3} maxLength={1000} value={form.comment}
                        onChange={(e) => setForm({ ...form, comment: e.target.value })} />
            </FormField>
            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="primary" type="submit">Post review</Button>
              <Button type="button" onClick={() => setParams({})}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          {!data?.items?.length && <p>You have not written any reviews yet. Open <strong>My Orders</strong> and choose “Write a review” on a delivered item.</p>}
          {(data?.items || []).map((r) => (
            <Card key={r.id} style={{ marginBottom: 12 }}>
              {editing?.id === r.id ? (
                <form onSubmit={saveEdit}>
                  <ErrorBox error={formError} />
                  {ratingSelect(editing.rating, (e) => setEditing({ ...editing, rating: e.target.value }), "rv-edit-rating")}
                  <FormField label="Your comment" id="rv-edit-comment">
                    <textarea id="rv-edit-comment" className="input" rows={3} maxLength={1000} value={editing.comment}
                              onChange={(e) => setEditing({ ...editing, comment: e.target.value })} />
                  </FormField>
                  <div style={{ display: "flex", gap: 8 }}>
                    <Button variant="primary" type="submit">Save</Button>
                    <Button type="button" onClick={() => setEditing(null)}>Cancel</Button>
                  </div>
                </form>
              ) : (
                <>
                  <h3>{r.product_title || "Product"} <Stars value={r.rating} /></h3>
                  {r.comment && <p>{r.comment}</p>}
                  <p className="muted">
                    {formatDate(r.created_at)}{" "}
                    {r.status === "hidden" && <Badge tone="red">hidden by an administrator</Badge>}
                  </p>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Button onClick={() => { setFormError(null); setEditing({ id: r.id, rating: String(r.rating), comment: r.comment || "" }); }}>Edit</Button>
                    <Button onClick={() => remove(r)}>Delete</Button>
                  </div>
                </>
              )}
            </Card>
          ))}
        </>
      )}
    </>
  );
}