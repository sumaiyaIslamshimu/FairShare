
import "./VerifiedBadge.css";

function VerifiedBadge({ verified }) {
  if (!verified) return null;

  return (
    <span className="verified-check" title="Verified seller">
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="20 6 9 17 4 12" />
      </svg>
      Verified
    </span>
  );
}

export default VerifiedBadge;
