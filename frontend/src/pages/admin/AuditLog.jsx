import { useState } from "react";
import { listAudit } from "../../api/admin.js";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const PAGE_SIZE = 25;

export default function AuditLog() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const { data, error, loading } = useLoad(() => listAudit({ action, page, page_size: PAGE_SIZE }), [action, page]);
  const columns = [
    { key: "at", header: "When", render: (e) => formatDate(e.at) },
    { key: "actor_email", header: "Admin" },
    { key: "action", header: "Action" },
    { key: "target", header: "Target" },
    { key: "details", header: "Details", render: (e) => (Object.keys(e.details || {}).length ? JSON.stringify(e.details) : "—") },
  ];
  return (
    <>
      <h1>Audit log</h1>
      <p className="subtitle">Admin actions and every access to a verification document. Entries cannot be edited here.</p>
      <input className="input" style={{ maxWidth: 260, marginBottom: 12 }} placeholder="Filter by action, e.g. verification." aria-label="Filter by action"
             value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }} />
      <ErrorBox error={error} />
      {loading && !data ? <Loading /> : (
        <>
          <DataTable columns={columns} rows={data?.items} emptyText="No entries." />
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
    </>
  );
}