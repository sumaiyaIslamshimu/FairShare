
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getUnreadCount } from "../api/notifications.js";
import { portalPath } from "../utils/portal.js";

const REFRESH_MS = 30000;

// The bell in the top bar. It checks for new notifications every 30 seconds.
// A failed check is ignored: the bell is a convenience and must never break the page.
export default function NotificationBell({ role }) {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let alive = true;

    const check = async () => {
      try {
        const r = await getUnreadCount();
        if (alive) setUnread(r.unread || 0);
      } catch {
        /* ignore */
      }
    };

    check();

    const timer = setInterval(check, REFRESH_MS);

    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const label = unread
    ? `Notifications, ${unread} unread`
    : "Notifications";

  return (
    <Link
      to={portalPath(role, "notifications")}
      aria-label={label}
      title={label}
      style={{
        position: "relative",
        textDecoration: "none",
        marginRight: 16,
      }}
    >
      <span aria-hidden="true" style={{ fontSize: 20 }}>
        🔔
      </span>

      {unread > 0 && (
        <span
          style={{
            position: "absolute",
            top: -6,
            right: -10,
            background: "#c0392b",
            color: "#fff",
            borderRadius: 10,
            fontSize: 11,
            padding: "1px 6px",
          }}
        >
          {unread > 99 ? "99+" : unread}
        </span>
      )}
    </Link>
  );
}