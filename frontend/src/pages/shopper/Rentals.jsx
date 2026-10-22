import { useEffect, useState } from "react";
import { browseRentals, submitRequest, getMyRequests } from "../../api/rentals.js";
import { formatPrice } from "../../utils/format.js";
import Button from "../../components/Button.jsx";

export default function ShopperRentals() {
  const [listings, setListings] = useState([]);
  const [requests, setRequests] = useState([]);
  const [dates, setDates] = useState({ start_date: "", end_date: "" });
  const [activeListing, setActiveListing] = useState(null);

  const fetchData = async () => {
    try {
      const pub = await browseRentals();
      setListings(pub.items);
      const reqs = await getMyRequests();
      setRequests(reqs.items);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRequest = async (e) => {
    e.preventDefault();
    try {
      await submitRequest({
        listing_id: activeListing.id,
        start_date: dates.start_date,
        end_date: dates.end_date
      });
      alert("Rental requested successfully!");
      setActiveListing(null);
      setDates({ start_date: "", end_date: "" });
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <h2>Rentals Platform</h2>

      <h3>Public Listings</h3>
      <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", marginBottom: "3rem" }}>
        {listings.map(item => (
          <div key={item.id} style={{ border: "1px solid #ccc", padding: "1rem", borderRadius: "5px" }}>
            <h4>{item.title}</h4>
            <p>{item.description}</p>
            <p><strong>Rate:</strong> {formatPrice(item.daily_rate_paisa, "BDT")} / day</p>
            <p><strong>Location:</strong> {item.location}</p>

            {activeListing?.id === item.id ? (
              <form onSubmit={handleRequest} style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "5px" }}>
                <input required type="date" value={dates.start_date} onChange={e => setDates({...dates, start_date: e.target.value})} />
                <input required type="date" value={dates.end_date} onChange={e => setDates({...dates, end_date: e.target.value})} />
                <div style={{ display: "flex", gap: "5px" }}>
                  <Button type="submit">Submit</Button>
                  <Button type="button" onClick={() => setActiveListing(null)} style={{ background: "#888" }}>Cancel</Button>
                </div>
              </form>
            ) : (
              <Button onClick={() => setActiveListing(item)} style={{ marginTop: "10px" }}>Request to Rent</Button>
            )}
          </div>
        ))}
      </div>

      <h3>My Rental Requests & Bookings</h3>
      {!requests.length && <p>You have no active rental requests.</p>}
      {requests.map(req => (
        <div key={req.id} style={{ border: "1px solid #ddd", padding: "10px", marginBottom: "10px" }}>
          <p><strong>Dates:</strong> {req.start_date} to {req.end_date}</p>
          <p><strong>Total:</strong> {formatPrice(req.total_paisa, "BDT")}</p>
          <p><strong>Status:</strong> <span style={{ textTransform: "uppercase", fontWeight: "bold" }}>{req.status}</span></p>
        </div>
      ))}
    </div>
  );
}