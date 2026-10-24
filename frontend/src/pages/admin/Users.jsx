import { useState } from "react";
import { listUsers, setUserActive } from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import useLoad from "../../hooks/useLoad.js";

const PAGE_SIZE = 20;

export default function Users() {
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState(null);
  const { data, error, loading, reload } = useLoad(
    () => listUsers({ q, role, page, page_size: PAGE_SIZE }),
    [q, role, page]
  );

  const toggle = async (u) => {
    setActionError(null);
    try {
      await setUserActive(u.id, !u.is_active);
      reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const columns = [
    { key: "full_name", header: "Name" },
    { key: "email", header: "Email" },
    { key: "role", header: "Role" },
    {
      key: "verification_status",
      header: "Identity",
      render: (u) => <Badge tone={u.verification_status === "approved" ? "green" : u.verification_status === "pending" ? "amber" : "neutral"}>{u.verification_status}</Badge>,
    },
    { key: "seller_status", header: "Seller", render: (u) => u.seller_status || "—" },
    { key: "is_active", header: "Account", render: (u) => <Badge tone={u.is_active ? "green" : "red"}>{u.is_active ? "active" : "suspended"}</Badge> },
    {
      key: "actions",
      header: "",
      render: (u) =>
        u.role === "admin" ? <span className="muted">protected</span> : (
          <Button onClick={() => toggle(u)}>{u.is_active ? "Suspend" : "Activate"}</Button>
        ),
    },
  ];

  return (
    <>
      <h1>Users</h1>
      <p className="subtitle">Suspending an account blocks it immediately, even if the person is logged in.</p>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input className="input" placeholder="Search name or email" value={q} aria-label="Search users"
               onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        <select className="input" value={role} aria-label="Filter by role" style={{ maxWidth: 160 }}
                onChange={(e) => { setRole(e.target.value); setPage(1); }}>
          <option value="">All roles</option>
          <option value="user">Shoppers</option>
          <option value="seller">Sellers</option>
          <option value="admin">Admins</option>
        </select>
      </div>
      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          <DataTable columns={columns} rows={data?.items} emptyText="No users match." />
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
    </>
  );
}