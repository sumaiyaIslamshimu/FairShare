// Shows a 1-5 rating as text that screen readers read correctly, e.g. "4 out of 5".
export default function Stars({ value }) {
  const n = Math.max(0, Math.min(5, Math.round(value || 0)));
  return (
    <span aria-label={`${value} out of 5`} title={`${value} out of 5`}>
      {"★".repeat(n)}{"☆".repeat(5 - n)}
    </span>
  );
}