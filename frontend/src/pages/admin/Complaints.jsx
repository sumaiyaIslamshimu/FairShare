import { useState } from "react";
import { listAdminComplaints, updateComplaint } from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import Modal from "../../components/Modal.jsx";
import Pagination from "../../components/Pagination.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const TONE = { open: "red", in_review: "amber", resolved: "green", dismissed: "neutral" };
const PAGE_SIZE = 20;

export default function Complaints() {
  const [status, setStatus] = useState("open");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ status: "in_review", admin_note: "" });
  const [actionError, setActionError] = useState(null);
  const { data, error, loading, reload } = useLoad(() => listAdminComplaints({ status, page, page_size: PAGE_SIZE }), [status, page]);

  const save = async () => {
    setActionError(null);
    try {
      await updateComplaint(editing.id, form);
      setEditing(null);
      reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const columns = [
    { key: "created_at", header: "Filed", render: (c) => formatDate(c.created_at) },
    { key: "filer_name", header: "By", render: (c) => <>{c.filer_name}<br /><small className="muted">{c.filer_email}</small></> },
    { key: "target_type", header: "About", render: (c) => <>{c.target_type}<br /><small className="muted">{c.target_id}</small></> },
    { key: "description", header: "Description" },
    { key: "status", header: "Status", render: (c) => <Badge tone={TONE[c.status]}>{c.status}</Badge> },
    { key: "actions", header: "", render: (c) => <Button onClick={() => { setEditing(c); setForm({ status: c.status, admin_note: c.admin_note || "" }); }}>Manage</Button> },
  ];

  return (
    <>
      <h1>Complaints</h1>
      <p className="subtitle">Complaints about orders, sellers and rentals. Your note is shown to the person who filed it.</p>
      <select className="input" aria-label="Complaint status" style={{ maxWidth: 180, marginBottom: 12 }} value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
        <option value="">All</option>
        <option value="open">Open</option>
        <option value="in_review">In review</option>
        <option value="resolved">Resolved</option>
        <option value="dismissed">Dismissed</option>
      </select>
      <ErrorBox error={error} />
      {loading && !data ? <Loading /> : (
        <>
          <DataTable columns={columns} rows={data?.items} emptyText="No complaints." />
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
      <Modal title="Manage complaint" open={!!editing} onClose={() => setEditing(null)}>
        <ErrorBox error={actionError} />
        <FormField label="Status" id="c-status">
          <select id="c-status" className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="open">Open</option>
            <option value="in_review">In review</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </FormField>
        <FormField label="Note to the person" id="c-note">
          <textarea id="c-note" className="input" rows={3} maxLength={1000} value={form.admin_note} onChange={(e) => setForm({ ...form, admin_note: e.target.value })} />
        </FormField>
        <Button variant="primary" onClick={save}>Save</Button>
      </Modal>
    </>
  );
}