import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthContext } from "../context/AuthContext.jsx";
import NotificationBell from "../components/NotificationBell.jsx";
import Notifications from "../pages/shared/Notifications.jsx";
import { NAV } from "../navConfig.js";
import { portalPath } from "../utils/portal.js";

const json = (data, status = 200) => Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(data) });
function mockApi(routes) {
  global.fetch = vi.fn((url, opts = {}) => {
    const key = `${opts.method || "GET"} ${String(url).replace(/^.*\/api/, "").split("?")[0]}`;
    const h = routes[key];
    if (!h) return json({ error: { code: "NOT_FOUND", message: `no mock for ${key}` } }, 404);
    return typeof h === "function" ? h(opts) : json(h);
  });
}
const Where = () => <div data-testid="where">{useLocation().pathname}</div>;
const wrap = (ui, role = "seller") => (
  <AuthContext.Provider value={{ user: { role }, loading: false }}>
    <MemoryRouter initialEntries={["/x"]}>
      <Routes>
        <Route path="/x" element={ui} />
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>
  </AuthContext.Provider>
);
afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

const n1 = { id: "n1", kind: "order", title: "You have a new order", body: "Order ORD-1", link: "orders", is_read: false, created_at: null };
const n2 = { id: "n2", kind: "x", title: "Old news", body: "", link: "", is_read: true, created_at: null };
const page = (items, unread) => ({ items, total: items.length, unread, page: 1, page_size: 20 });

describe("notifications", () => {
  it("links to the right portal for every role and sits in every navigation", () => {
    expect(portalPath("user", "orders")).toBe("/app/orders");
    expect(portalPath("seller", "returns")).toBe("/seller/returns");
    expect(portalPath("admin", "notifications")).toBe("/admin/notifications");
    expect(NAV.user.map((i) => i.to)).toContain("/app/notifications");
    expect(NAV.seller.map((i) => i.to)).toContain("/seller/notifications");
    expect(NAV.admin.map((i) => i.to)).toContain("/admin/notifications");
  });

  it("the bell shows the unread count and links to the person's own page", async () => {
    mockApi({ "GET /notifications/unread-count": { unread: 3 } });
    render(wrap(<NotificationBell role="seller" />));
    const link = await screen.findByRole("link", { name: "Notifications, 3 unread" });
    expect(link).toHaveAttribute("href", "/seller/notifications");
  });

  it("the bell survives a failing server and shows no count", async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error("offline")));
    render(wrap(<NotificationBell role="user" />));
    expect(await screen.findByRole("link", { name: "Notifications" })).toBeInTheDocument();
  });

  it("the bell checks again every 30 seconds and stops after unmount", async () => {
    vi.useFakeTimers();
    mockApi({ "GET /notifications/unread-count": { unread: 0 } });
    const { unmount } = render(wrap(<NotificationBell role="user" />));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    const first = global.fetch.mock.calls.length;
    await act(async () => { await vi.advanceTimersByTimeAsync(30000); });
    expect(global.fetch.mock.calls.length).toBe(first + 1);
    unmount();
    await act(async () => { await vi.advanceTimersByTimeAsync(60000); });
    expect(global.fetch.mock.calls.length).toBe(first + 1);
  });

  it("opening a notification marks it read and goes to its page", async () => {
    mockApi({ "GET /notifications": page([n1, n2], 1), "POST /notifications/n1/read": { ...n1, is_read: true } });
    render(wrap(<Notifications />));
    expect(await screen.findByText("You have a new order")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Open" })[0]);
    await waitFor(() => expect(screen.getByTestId("where")).toHaveTextContent("/seller/orders"));
    expect(global.fetch.mock.calls.some(([u, o]) => String(u).endsWith("/notifications/n1/read") && o.method === "POST")).toBe(true);
  });

  it("mark all as read calls the API and is disabled when nothing is unread", async () => {
    mockApi({ "GET /notifications": page([n2], 0) });
    render(wrap(<Notifications />));
    expect(await screen.findByText("Old news")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark all as read" })).toBeDisabled();
  });

  it("mark all as read works when there is something unread", async () => {
    mockApi({ "GET /notifications": page([n1], 1), "POST /notifications/read-all": { marked: 1 } });
    render(wrap(<Notifications />));
    fireEvent.click(await screen.findByRole("button", { name: "Mark all as read" }));
    await waitFor(() => expect(global.fetch.mock.calls.some(([u, o]) => String(u).endsWith("/notifications/read-all") && o.method === "POST")).toBe(true));
  });

  it("the unread-only box asks the server for unread items", async () => {
    mockApi({ "GET /notifications": page([], 0) });
    render(wrap(<Notifications />));
    fireEvent.click(await screen.findByLabelText(/Unread only/));
    await waitFor(() => expect(global.fetch.mock.calls.some(([u]) => String(u).includes("unread_only=true"))).toBe(true));
    expect(await screen.findByText("Nothing unread.")).toBeInTheDocument();
  });
});