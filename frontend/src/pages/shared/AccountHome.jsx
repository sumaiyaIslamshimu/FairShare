import Badge from "../../components/Badge.jsx";
import StatCard from "../../components/StatCard.jsx";
import { useAuth } from "../../context/AuthContext.jsx";

const VERIFY_TONE = { approved: "green", pending: "amber", rejected: "red", none: "neutral" };

export default function AccountHome() {
  const { user } = useAuth();
  const first = user.full_name.split(" ")[0];
  return (
    <>
      <h1>Welcome, {first}</h1>
      <p className="subtitle">Your FairShare account at a glance. More tools appear here as each module is added.</p>
      {user.role === "seller" && user.seller_status !== "approved" && (
        <div className="info-box">
          Your seller account is <strong>{user.seller_status}</strong>. An administrator must approve it before you can publish listings.
        </div>
      )}
      <div className="stat-grid">
        <StatCard label="Account type" value={user.role} />
        <StatCard label="Email" value={user.email} />
        <StatCard label="Identity verification" value={<Badge tone={VERIFY_TONE[user.verification_status]}>{user.verification_status}</Badge>} />
        {user.role === "seller" && (
          <StatCard label="Seller approval" value={<Badge tone={user.seller_status === "approved" ? "green" : "amber"}>{user.seller_status}</Badge>} />
        )}
      </div>
    </>
  );
}