import { Link } from "react-router-dom";
import { getStats } from "../../api/admin.js";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import StatCard from "../../components/StatCard.jsx";
import useLoad from "../../hooks/useLoad.js";

export default function Dashboard() {
  const { data: s, error, loading } = useLoad(getStats);
  if (loading) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  const todo = [
    { to: "/admin/verification", n: s.verifications.pending, label: "identity verifications waiting" },
    { to: "/admin/verification", n: s.sellers.pending, label: "seller accounts pending" },
    { to: "/admin/complaints", n: s.complaints.open, label: "open complaints" },
  ];
  return (
    <>
      <h1>Admin dashboard</h1>
      <p className="subtitle">Live counts from the database. Nothing on this page is sample data.</p>
      <div className="stat-grid">
        <StatCard label="Users" value={s.users.total}>
          <small className="muted">{s.users.shoppers} shoppers · {s.users.sellers} sellers · {s.users.suspended} suspended</small>
        </StatCard>
        <StatCard label="FairShare listings" value={s.products.fairshare}>
          <small className="muted">{s.products.hidden} hidden · {s.products.external} external (comparison only)</small>
        </StatCard>
        <StatCard label="Orders" value={s.orders.total}>
          <small className="muted">{s.orders.pending} pending</small>
        </StatCard>
        <StatCard label="Rentals" value={s.rentals.listings}>
          <small className="muted">{s.rentals.requests} requests · {s.rentals.bookings} bookings</small>
        </StatCard>
        <StatCard label="Complaints" value={s.complaints.total}>
          <small className="muted">{s.complaints.open} open · {s.complaints.in_review} in review</small>
        </StatCard>
        <StatCard label="Store sources" value={s.scraping.stores}>
          <small className="muted">
            {Object.entries(s.scraping.by_status).map(([k, v]) => `${v} ${k}`).join(" · ") || "none"}
          </small>
        </StatCard>
      </div>
      <Card style={{ marginTop: 16 }}>
        <h2>Needs attention</h2>
        <ul>
          {todo.map((t) => (
            <li key={t.label}>
              <Link to={t.to}><strong>{t.n}</strong> {t.label}</Link>
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}