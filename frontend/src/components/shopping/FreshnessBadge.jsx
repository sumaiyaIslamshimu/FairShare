import Badge from "../Badge.jsx";

const LABELS = {
  fresh: ["green", "Recently updated"],
  stale: ["amber", "Possibly outdated"],
  unavailable: ["red", "Unavailable"],
};

export default function FreshnessBadge({ freshness, source }) {
  if (source === "fairshare") return <Badge tone="green">Live listing</Badge>;
  const [tone, text] = LABELS[freshness] || ["neutral", "Unknown"];
  return <Badge tone={tone}>{text}</Badge>;
}