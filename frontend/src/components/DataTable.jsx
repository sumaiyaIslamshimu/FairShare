import EmptyState from "./EmptyState.jsx";

// columns: [{ key, header, render?: (row) => node }]
export default function DataTable({ columns, rows, emptyText = "Nothing to show yet." }) {
  if (!rows || rows.length === 0) return <EmptyState title={emptyText} />;
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>{columns.map((c) => <th key={c.key}>{c.header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id || i}>
              {columns.map((c) => <td key={c.key}>{c.render ? c.render(row) : row[c.key]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}