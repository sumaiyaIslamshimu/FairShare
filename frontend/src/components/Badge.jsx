// tone: "neutral" | "green" | "red" | "amber"
export default function Badge({ tone = "neutral", children }) {
  const toneClass = tone === "neutral" ? "" : `badge-${tone}`;
  return <span className={`badge ${toneClass}`.trim()}>{children}</span>;
}