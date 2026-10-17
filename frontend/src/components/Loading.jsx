export default function Loading({ text = "Loading…" }) {
  return <div className="loading" role="status">{text}</div>;
}