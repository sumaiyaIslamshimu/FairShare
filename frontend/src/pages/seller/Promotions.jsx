import { useEffect, useState } from "react";
import { getPromotions, createPromotion, deletePromotion } from "../../api/seller.js";
import { formatDate } from "../../utils/format.js";
import Button from "../../components/Button.jsx";

export default function Promotions() {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: "", product_ids: "", discount_percent: 10, starts_at: "", ends_at: "" });
  const [error, setError] = useState("");

  const fetchPromotions = async () => {
    try {
      const data = await getPromotions();
      setPromotions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPromotions();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        ...form,
        product_ids: form.product_ids.split(",").map(id => id.trim()),
        starts_at: new Date(form.starts_at).toISOString(),
        ends_at: new Date(form.ends_at).toISOString()
      };
      await createPromotion(payload);
      setForm({ name: "", product_ids: "", discount_percent: 10, starts_at: "", ends_at: "" });
      fetchPromotions();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this promotion?")) return;
    try {
      await deletePromotion(id);
      fetchPromotions();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Manage Promotions</h2>
      {error && <div style={{ color: "red", marginBottom: "1rem" }}>{error}</div>}

      <div style={{ padding: "1rem", background: "#f9f9f9", marginBottom: "2rem" }}>
        <h3>Create New Promotion</h3>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "10px", maxWidth: "500px" }}>
          <input required type="text" placeholder="Promo Name (e.g., Eid Sale)" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
          <input required type="text" placeholder="Product IDs (comma separated)" value={form.product_ids} onChange={e => setForm({...form, product_ids: e.target.value})} />
          <input required type="number" min="1" max="90" placeholder="Discount %" value={form.discount_percent} onChange={e => setForm({...form, discount_percent: parseInt(e.target.value)})} />
          <label>Start Date</label>
          <input required type="datetime-local" value={form.starts_at} onChange={e => setForm({...form, starts_at: e.target.value})} />
          <label>End Date</label>
          <input required type="datetime-local" value={form.ends_at} onChange={e => setForm({...form, ends_at: e.target.value})} />
          <Button type="submit">Create Promotion</Button>
        </form>
      </div>

      <h3>Active & Upcoming Promotions</h3>
      {promotions.map(promo => (
        <div key={promo.id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem" }}>
          <h4>{promo.name} <span style={{ color: promo.is_active ? "green" : "red" }}>({promo.discount_percent}% OFF)</span></h4>
          <p>Products: {promo.product_ids.join(", ")}</p>
          <p>Runs: {formatDate(promo.starts_at)} to {formatDate(promo.ends_at)}</p>
          <Button onClick={() => handleDelete(promo.id)} style={{ background: "red", marginTop: "10px" }}>Delete</Button>
        </div>
      ))}
    </div>
  );
}