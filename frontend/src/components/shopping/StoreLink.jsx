export default function StoreLink({ url, children }) {
  if (typeof url !== "string" || !/^https?:\/\//i.test(url)) {
    return <span className="muted">Link not available</span>;
  }
  return (
    <a href={url} target="_blank" rel="noopener noreferrer">
      {children} ↗
    </a>
  );
}