import { useState } from "react";
import { listSellerReviews } from "../../api/reviews.js";
import Card from "../../components/Card.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import Stars from "../../components/Stars.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const PAGE_SIZE = 20;

export default function Reviews() {
  const [page, setPage] = useState(1);
  const { data, error, loading } = useLoad(() => listSellerReviews(page), [page]);
  const columns = [
    { key: "created_at", header: "Date", render: (r) => formatDate(r.created_at) },
    { key: "product_title", header: "Product" },
    { key: "rating", header: "Rating", render: (r) => <Stars value={r.rating} /> },
    { key: "comment", header: "Comment", render: (r) => r.comment || "—" },
    { key: "reviewer_name", header: "By" },
  ];
  return (
    <>
      <h1>Customer reviews</h1>
      <p className="subtitle">Reviews from shoppers whose order you delivered. Reviews hidden by an administrator are not shown or counted.</p>
      <ErrorBox error={error} />
      {loading && !data ? <Loading /> : (
        <Card>
          <p><strong>Average rating:</strong> {data?.average ? <><Stars value={data.average} /> {data.average} ({data.total})</> : "No reviews yet"}</p>
          <DataTable columns={columns} rows={data?.items} emptyText="No reviews yet." />
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </Card>
      )}
    </>
  );
}