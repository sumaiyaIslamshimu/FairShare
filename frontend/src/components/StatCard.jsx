import Card from "./Card.jsx";

export default function StatCard({ label, value, children }) {
  return (
    <Card className="stat-card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {children}
    </Card>
  );
}