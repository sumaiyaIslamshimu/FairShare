import { useState } from "react";
import { listAdminProducts, listAdminRentals, moderateProduct, moderateRental } from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatPrice } from "../../utils/format.js";

export default function Listings() {
  const [tab, setTab] = useState("products");
  const [q, setQ] = useState("");
  const [actionError, setActionError] = useState(null);
  const products = useLoad(() => (tab === "products" ? listAdminProducts({ q, page_size: 50 }) : Promise.resolve(null)), [tab, q]);
  const rentals = useLoad(() => (tab === "rentals" ? listAdminRentals({ q, page_size: 50 }) : Promise.resolve(null)), [tab, q]);

  const act = async (fn) => {
    setActionError(null);
    try {
      await fn();
      products.reload();
      rentals.reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const productColumns = [
    { key: "title", header: "Product" },
    { key: "seller_name", header: "Seller" },
    { key: "price_paisa", header: "Price", render: (p) => formatPrice(p.price_paisa, "BDT") },
    { key: "stock_qty", header: "Stock" },
    { key: "moderation_status", header: "Visibility", render: (p) => <Badge tone={p.moderation_status === "visible" ? "green" : "red"}>{p.moderation_status}</Badge> },
    {
      key: "actions", header: "",
      render: (p) => (
        <div style={{ display: "flex", gap: 6 }}>
          {p.moderation_status === "visible"
            ? <Button onClick={() => act(() => moderateProduct(p.id, "hidden"))}>Hide</Button>
            : <Button onClick={() => act(() => moderateProduct(p.id, "visible"))}>Show</Button>}
          <Button onClick={() => window.confirm("Remove this listing for good?") && act(() => moderateProduct(p.id, "removed"))}>Remove</Button>
        </div>
      ),
    },
  ];

  const rentalColumns = [
    { key: "title", header: "Rental listing" },
    { key: "owner_name", header: "Owner" },
    { key: "location", header: "Location" },
    { key: "daily_rate_paisa", header: "Per day", render: (r) => formatPrice(r.daily_rate_paisa, "BDT") },
    { key: "status", header: "Status", render: (r) => <Badge tone={r.status === "active" ? "green" : "amber"}>{r.status}</Badge> },
    {
      key: "actions", header: "",
      render: (r) => (
        <div style={{ display: "flex", gap: 6 }}>
          {r.status === "active"
            ? <Button onClick={() => act(() => moderateRental(r.id, "inactive"))}>Deactivate</Button>
            : <Button onClick={() => act(() => moderateRental(r.id, "active"))}>Activate</Button>}
          <Button onClick={() => window.confirm("Remove this rental listing?") && act(() => moderateRental(r.id, "removed"))}>Remove</Button>
        </div>
      ),
    },
  ];

  const current = tab === "products" ? products : rentals;
  return (
    <>
      <h1>Listing moderation</h1>
      <p className="subtitle">Shopping listings and rental listings are separate. Hidden items leave the shop and cannot be bought.</p>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <Button variant={tab === "products" ? "primary" : "outline"} onClick={() => setTab("products")}>FairShare products</Button>
        <Button variant={tab === "rentals" ? "primary" : "outline"} onClick={() => setTab("rentals")}>Rental listings</Button>
        <input className="input" placeholder="Search title" aria-label="Search listings" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <ErrorBox error={actionError || current.error} />
      {current.loading && !current.data ? <Loading /> : (
        <DataTable columns={tab === "products" ? productColumns : rentalColumns} rows={current.data?.items} emptyText="Nothing to moderate." />
      )}
    </>
  );
}