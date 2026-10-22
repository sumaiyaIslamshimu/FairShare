import { useEffect, useState } from "react";
import { getMyListings, createListing, getIncomingRequests, decideRequest } from "../../api/rentals.js";
import { formatPrice } from "../../utils/format.js";
import Button from "../../components/Button.jsx";

export default function SellerRentals() {
  const [listings, setListings] = useState([]);
  const [requests, setRequests] = useState([]);
  const [form, setForm] = useState({ title: "", description: "", daily_rate_paisa: 1000, deposit_paisa: 0, location: "" });

  const fetchData = async () => {
    try {
      const list = await getMyListings();
      setListings(list.items);
      const reqs = await getIncomingRequests();
      setRequests(reqs.items);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createListing({
        ...form,
        daily_rate_paisa: parseInt(form.daily_rate_paisa),
        deposit_paisa: parseInt(form.deposit_paisa)
      });
      setForm({ title: "", description: "", daily_rate_paisa: 1000, deposit_paisa: 0, location: "" });
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDecision = async (id, action) => {
    try {
      await decideRequest(id, action);
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <h2>Manage Rentals</h2>

      <div style={{ padding: "1rem", background: "#f9f9f9", marginBottom: "2rem" }}>
        <h3>Create New Listing</h3>
        <form onSubmit={handleCreate} style={{ display: "grid", gap: "10px", maxWidth: "500px" }}>
          <input required type="text" placeholder="Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
          <textarea required placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
          <input required type="number" placeholder="Daily Rate (paisa)" value={form.daily_rate_paisa} onChange={e => setForm({...form, daily_rate_paisa: e.target.value})} />
          <input required type="number" placeholder="Deposit (paisa)" value={form.deposit_paisa} onChange={e => setForm({...form, deposit_paisa: e.target.value})} />
          <input required type="text" placeholder="Location" value={form.location} onChange={e => setForm({...form, location: e.target.value})} />
          <Button type="submit">Publish Listing</Button>
        </form>
      </div>

      <h3>Incoming Requests</h3>
      {!requests.length && <p>No incoming requests.</p>}
      {requests.map(req => (
        <div key={req.id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem" }}>
          <p><strong>Dates:</strong> {req.start_date} to {req.end_date}</p>
          <p><strong>Total:</strong> {formatPrice(req.total_paisa, "BDT")}</p>
          <p><strong>Status:</strong> {req.status}</p>
          {req.status === "pending" && (
            <div style={{ marginTop: "10px", display: "flex", gap: "10px" }}>
              <Button onClick={() => handleDecision(req.id, "accept")} style={{ background: "green" }}>Accept</Button>
              <Button onClick={() => handleDecision(req.id, "reject")} style={{ background: "red" }}>Reject</Button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}