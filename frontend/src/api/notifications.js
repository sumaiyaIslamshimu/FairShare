import { request } from "./client.js";

export function listNotifications({ unreadOnly = false, page = 1 } = {}) {
  const q = new URLSearchParams({ page: String(page) });
  if (unreadOnly) q.set("unread_only", "true");
  const query = q.toString();
  return request(`/notifications?${query}`);
}
export const getUnreadCount = () => request("/notifications/unread-count");
export const markNotificationRead = (id) => request(`/notifications/${id}/read`, { method: "POST" });
export const markAllNotificationsRead = () => request("/notifications/read-all", { method: "POST" });