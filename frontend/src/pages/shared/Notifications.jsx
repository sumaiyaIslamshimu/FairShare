import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../../api/notifications.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";
import { portalPath } from "../../utils/portal.js";

const PAGE_SIZE = 20;

export default function Notifications() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [actionError, setActionError] = useState(null);
  const { data, error, loading, reload } = useLoad(() => listNotifications({ unreadOnly, page }), [unreadOnly, page]);

  const open = async (n) => {
    setActionError(null);
    try {
      if (!n.is_read) await markNotificationRead(n.id);
      if (n.link) navigate(portalPath(user?.role, n.link));
      else reload();
    } catch (e) {
      setActionError(e);
    }
  };

  const readAll = async () => {
    setActionError(null);
    try {
      await markAllNotificationsRead();
      reload();
    } catch (e) {
      setActionError(e);
    }
  };

  return (
    <>
      <h1>Notifications</h1>
      <p className="subtitle">Updates about your orders, returns, reviews, complaints and account. These appear here only; nothing is emailed or texted.</p>
      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <label>
          <input type="checkbox" checked={unreadOnly} onChange={(e) => { setUnreadOnly(e.target.checked); setPage(1); }} /> Unread only
        </label>
        <Button onClick={readAll} disabled={!data?.unread}>Mark all as read</Button>
        {data && <span className="muted">{data.unread} unread</span>}
      </div>
      <ErrorBox error={error || actionError} />
      {loading && !data ? <Loading /> : (
        <>
          {!data?.items?.length && <p>{unreadOnly ? "Nothing unread." : "You have no notifications yet."}</p>}
          {(data?.items || []).map((n) => (
            <Card key={n.id} style={{ marginBottom: 8, opacity: n.is_read ? 0.75 : 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <div>
                  <strong>{n.title}</strong> {!n.is_read && <Badge tone="amber">new</Badge>}
                  {n.body && <p style={{ margin: "4px 0" }}>{n.body}</p>}
                  <small className="muted">{formatDate(n.created_at)}</small>
                </div>
                <Button onClick={() => open(n)}>{n.link ? "Open" : n.is_read ? "Read" : "Mark read"}</Button>
              </div>
            </Card>
          ))}
          <Pagination page={page} pageSize={PAGE_SIZE} total={data?.total || 0} onChange={setPage} />
        </>
      )}
    </>
  );
}