import { useState } from "react";
import Badge from "./Badge.jsx";
import Button from "./Button.jsx";
import DataTable from "./DataTable.jsx";
import ErrorBox from "./ErrorBox.jsx";
import FormField from "./FormField.jsx";
import Loading from "./Loading.jsx";
import Modal from "./Modal.jsx";
import Pagination from "./Pagination.jsx";
import useLoad from "../hooks/useLoad.js";
import { formatDate, formatPrice } from "../utils/format.js";

export const RETURN_TONE = { requested: "amber", approved: "green", completed: "green", rejected: "red", cancelled: "neutral" };
export const REASON_LABEL = {
  damaged: "Damaged", wrong_item: "Wrong item", not_as_described: "Not as described", changed_mind: "Changed my mind", other: "Other",
};
const PAGE_SIZE = 20;

// Used by the seller page and the admin page: same table, different API functions.
export default function ReturnsTable({ load, decide }) {
  const [status, setStatus] = useState("requested");
  const [page, setPage] = useState(1);
  const [rejecting, setRejecting] = useState(null);
  const [note, setNote] = useState("");
  const [actionError, setActionError] = useState(null);
  const { data, error, loading, reload } = useLoad(() => load({ status, page, page_size: PAGE_SIZE }), [status, page]);

  const run = async (fn) => {
    setActionError(null);
    try {
      await fn();
      reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const columns = [
    { key: "created_at", header: "Asked", render: (r) => formatDate(r.created_at) },
    { key: "shopper_name", header: "Shopper", render: (r) => <>{r.shopper_name}<br /><small className="muted">{r.shopper_email}</small></> },
    { key: "product_title", header: "Item", render: (r) => `${r.quantity}x ${r.product_title}` },
    { key: "reason", header: "Reason", render: (r) => <>{REASON_LABEL[r.reason] || r.reason}{r.details && <><br /><small className="muted">{r.details}</small></>}</> },
    { key: "refund_paisa", header: "Refund (simulated)", render: (r) => formatPrice(r.refund_paisa, r.currency) },
    { key: "status", header: "Status", render: (r) => <Badge tone={RETURN_TONE[r.status]}>{r.status}</Badge> },
    {
      key: "actions", header: "",
      render: (r) => (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {r.status === "requested" && (
            <>
              <Button variant="primary" onClick={() => run(() => decide(r.id, "approve"))}>Approve</Button>
              <Button onClick={() => { setRejecting(r); setNote(""); }}>Reject</Button>
            </>
          )}
          {r.status === "approved" && (
            <Button variant="primary" onClick={() => run(() => decide(r.id, "complete"))}>Mark received &amp; restock</Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <select className="input" aria-label="Return status" style={{ maxWidth: 180, marginBottom: 12 }} value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
        <option value="">All</option>
        <option value="requested">Requested</option>
        <option value="approved">Approved</option>
        <option value="completed">Completed</option>
        <option value="rejected">Rejected</option>
        <option value="cancelled">Cancelled</option>
      </select>
      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          <DataTable columns={columns} rows={data?.items} emptyText="No return requests." />
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
      <Modal title="Reject return" open={!!rejecting} onClose={() => setRejecting(null)}>
        <FormField label="Reason (shown to the shopper)" id="ret-note">
          <textarea id="ret-note" className="input" rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
        </FormField>
        <Button variant="primary" disabled={!note.trim()}
                onClick={() => run(async () => { await decide(rejecting.id, "reject", note); setRejecting(null); })}>Reject</Button>
      </Modal>
    </>
  );
}