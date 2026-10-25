import { useState } from "react";
import { listAdminReviews, moderateReview } from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import Stars from "../../components/Stars.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const PAGE_SIZE = 20;

export default function Reviews() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState(null);
  const { data, error, loading, reload } = useLoad(() => listAdminReviews({ status, page, page_size: PAGE_SIZE }), [status, page]);

  const set = async (r, next) => {
    setActionError(null);
    try {
      await moderateReview(r.id, next);
      reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const columns = [
    { key: "created_at", header: "Date", render: (r) => formatDate(r.created_at) },
    { key: "product_title", header: "Product" },
    { key: "rating", header: "Rating", render: (r) => <Stars value={r.rating} /> },
    { key: "comment", header: "Comment", render: (r) => r.comment || "—" },
    { key: "reviewer_email", header: "Reviewer" },
    { key: "status", header: "Status", render: (r) => <Badge tone={r.status === "visible" ? "green" : "red"}>{r.status}</Badge> },
    {
      key: "actions", header: "",
      render: (r) => (r.status === "visible"
        ? <Button onClick={() => set(r, "hidden")}>Hide</Button>
        : <Button onClick={() => set(r, "visible")}>Show</Button>),
    },
  ];

  return (
    <>
      <h1>Review moderation</h1>
      <p className="subtitle">Hide reviews that are abusive or false. A hidden review no longer shows or counts toward the average. Every change is audit-logged.</p>
      <select className="input" aria-label="Review status" style={{ maxWidth: 180, marginBottom: 12 }} value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
        <option value="">All</option>
        <option value="visible">Visible</option>
        <option value="hidden">Hidden</option>
      </select>
      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          <DataTable columns={columns} rows={data?.items} emptyText="No reviews." />
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
    </>
  );
}