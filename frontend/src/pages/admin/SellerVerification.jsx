import { useState } from "react";
import { decideVerification, fetchVerificationDocument, listSellers, listVerifications, setSellerStatus } from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import Modal from "../../components/Modal.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const TONE = { approved: "green", pending: "amber", rejected: "red", suspended: "red" };

export default function SellerVerification() {
  const [status, setStatus] = useState("pending");
  const [sellerFilter, setSellerFilter] = useState("");
  const [rejecting, setRejecting] = useState(null);
  const [note, setNote] = useState("");
  const [actionError, setActionError] = useState(null);
  const ver = useLoad(() => listVerifications({ status, page_size: 50 }), [status]);
  const sellers = useLoad(() => listSellers({ status: sellerFilter, page_size: 50 }), [sellerFilter]);

  const run = async (fn) => {
    setActionError(null);
    try {
      await fn();
      ver.reload();
      sellers.reload();
    } catch (e) {
      setActionError(e);
    }
  };

  // The document is private: it is fetched with the admin's token (each view is audit-logged) and opened in a new tab.
  const viewDocument = (rec) => run(async () => {
    const blob = await fetchVerificationDocument(rec.id);
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener");
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  });

  const submitReject = () => run(async () => {
    await decideVerification(rejecting.id, "reject", note);
    setRejecting(null);
    setNote("");
  });

  const verColumns = [
    { key: "user_name", header: "Person", render: (r) => <>{r.user_name}<br /><small className="muted">{r.user_email} · {r.user_role}</small></> },
    { key: "nid_masked", header: "NID (masked)", render: (r) => <code>{r.nid_masked}</code> },
    { key: "submitted_at", header: "Submitted", render: (r) => formatDate(r.submitted_at) },
    { key: "status", header: "Status", render: (r) => <Badge tone={TONE[r.status]}>{r.status}</Badge> },
    {
      key: "actions", header: "",
      render: (r) => (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {r.has_document && <Button onClick={() => viewDocument(r)}>View document</Button>}
          {r.status === "pending" && (
            <>
              <Button variant="primary" onClick={() => run(() => decideVerification(r.id, "approve"))}>Approve</Button>
              <Button onClick={() => { setRejecting(r); setNote(""); }}>Reject</Button>
            </>
          )}
        </div>
      ),
    },
  ];

  const sellerColumns = [
    { key: "business_name", header: "Business" },
    { key: "email", header: "Owner", render: (s) => <>{s.full_name}<br /><small className="muted">{s.email}</small></> },
    { key: "verification_status", header: "Identity", render: (s) => <Badge tone={TONE[s.verification_status]}>{s.verification_status}</Badge> },
    { key: "status", header: "Seller status", render: (s) => <Badge tone={TONE[s.status]}>{s.status}</Badge> },
    {
      key: "actions", header: "",
      render: (s) => (
        <div style={{ display: "flex", gap: 6 }}>
          {s.status !== "approved" && <Button variant="primary" onClick={() => run(() => setSellerStatus(s.user_id, "approved"))}>Approve</Button>}
          {s.status !== "suspended" && <Button onClick={() => run(() => setSellerStatus(s.user_id, "suspended"))}>Suspend</Button>}
        </div>
      ),
    },
  ];

  return (
    <>
      <h1>Verification &amp; sellers</h1>
      <p className="subtitle">
        Manual review. NID numbers are masked; open the document only when you need to. Every document view is recorded in the audit log.
      </p>
      <ErrorBox error={actionError || ver.error || sellers.error} />

      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Identity verification</h2>
          <select className="input" aria-label="Verification status" style={{ maxWidth: 160 }} value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="">All</option>
          </select>
        </div>
        {ver.loading && !ver.data ? <Loading /> : <DataTable columns={verColumns} rows={ver.data?.items} emptyText="No records." />}
      </Card>

      <Card style={{ marginTop: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Seller accounts</h2>
          <select className="input" aria-label="Seller status" style={{ maxWidth: 160 }} value={sellerFilter} onChange={(e) => setSellerFilter(e.target.value)}>
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>
        <p className="muted">A seller can only be approved after their identity is approved. Approving a seller&apos;s identity approves their pending seller account.</p>
        {sellers.loading && !sellers.data ? <Loading /> : <DataTable columns={sellerColumns} rows={sellers.data?.items} emptyText="No sellers." />}
      </Card>

      <Modal title="Reject verification" open={!!rejecting} onClose={() => setRejecting(null)}>
        <FormField label="Reason (shown to the person so they can fix it)" id="reject-note">
          <textarea id="reject-note" className="input" rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
        </FormField>
        <Button variant="primary" disabled={!note.trim()} onClick={submitReject}>Reject</Button>
      </Modal>
    </>
  );
}