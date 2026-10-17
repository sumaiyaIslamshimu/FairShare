import Button from "./Button.jsx";

export default function Pagination({ page, pageSize, total, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="pagination">
      <span className="muted">Page {page} of {pages}</span>
      <Button disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</Button>
      <Button disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</Button>
    </div>
  );
}