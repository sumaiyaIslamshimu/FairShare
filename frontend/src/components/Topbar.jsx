import NotificationBell from "./NotificationBell.jsx";

export default function Topbar({ title, user }) {
  const initials = (user?.full_name || "?").split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  return (
    <header className="topbar">
      <strong>{title}</strong>
      <div style={{ display: "flex", alignItems: "center" }}>
        {user?.role && <NotificationBell role={user.role} />}
        <div className="user-chip">
          <div className="avatar">{initials}</div>
          <div>
            {user?.full_name}
            <small>{user?.role}</small>
          </div>
        </div>
      </div>
    </header>
  );
}