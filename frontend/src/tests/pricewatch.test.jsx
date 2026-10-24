import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import TrackButton from "../components/shopping/TrackButton.jsx";
import PriceWatch from "../pages/shopper/PriceWatch.jsx";
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
afterEach(() => vi.restoreAllMocks());

const item = { id: "p1", source: "external", name: "Rice 5 kg" };
const w = {
  id: "w1", source: "external", product_id: "p1", name: "Rice 5 kg", store_name: "Daraz", store_url: "https://daraz.test/p/1",
  currency: "BDT", availability: "in_stock", freshness: "fresh", price_when_added_paisa: 70000, current_price_paisa: 65000,
  lowest_seen_paisa: 65000, target_price_paisa: 60000, change_paisa: -5000, status: "dropped", created_at: null,
};
const page = (items) => ({ items, total: items.length, page: 1, page_size: 20 });

describe("price tracking", () => {
  it("is in the shopper navigation and notifications land on the page", () => {
    expect(NAV.user.map((i) => i.to)).toContain("/app/pricewatch");
    expect(portalPath("user", "pricewatch")).toBe("/app/pricewatch");
  });

  it("the track button sends the target in paisa and then says it is tracking", async () => {
    vi.spyOn(window, "prompt").mockReturnValue("600");
    mockApi({ "POST /watches": w });
    render(<TrackButton item={item} />);
    fireEvent.click(screen.getByRole("button", { name: "Track price" }));
    expect(await screen.findByText(/Tracking this price/)).toBeInTheDocument();
    const call = global.fetch.mock.calls.find(([, o]) => o?.method === "POST");
    expect(JSON.parse(call[1].body)).toEqual({ source: "external", product_id: "p1", target_price_paisa: 60000 });
  });

  it("an empty answer means any drop, and cancel sends nothing", async () => {
    const prompt = vi.spyOn(window, "prompt").mockReturnValue("");
    mockApi({ "POST /watches": w });
    const { unmount } = render(<TrackButton item={item} />);
    fireEvent.click(screen.getByRole("button", { name: "Track price" }));
    await screen.findByText(/Tracking this price/);
    expect(JSON.parse(global.fetch.mock.calls[0][1].body)).toEqual({ source: "external", product_id: "p1" });
    unmount();
    prompt.mockReturnValue(null);
    global.fetch.mockClear();
    render(<TrackButton item={item} />);
    fireEvent.click(screen.getByRole("button", { name: "Track price" }));
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("shows the server's refusal, and treats 'already tracking' as success", async () => {
    vi.spyOn(window, "prompt").mockReturnValue("900");
    mockApi({ "POST /watches": () => json({ error: { code: "TARGET_TOO_HIGH", message: "Choose a target below the current price." } }, 422) });
    const { unmount } = render(<TrackButton item={item} />);
    fireEvent.click(screen.getByRole("button", { name: "Track price" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/below the current price/);
    unmount();
    mockApi({ "POST /watches": () => json({ error: { code: "ALREADY_WATCHING", message: "x" } }, 409) });
    render(<TrackButton item={item} />);
    fireEvent.click(screen.getByRole("button", { name: "Track price" }));
    expect(await screen.findByText(/Tracking this price/)).toBeInTheDocument();
  });

  it("lists watches with current, start, lowest and target prices", async () => {
    mockApi({ "GET /watches": page([w]) });
    render(<MemoryRouter><PriceWatch /></MemoryRouter>);
    expect(await screen.findByText("Rice 5 kg")).toBeInTheDocument();
    expect(screen.getByText("Cheaper than when you started")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open store page" })).toHaveAttribute("href", "https://daraz.test/p/1");
    expect(screen.getByText(/Your target/)).toBeInTheDocument();
  });

  it("an unavailable offer shows 'Not available', never an invented price", async () => {
    mockApi({ "GET /watches": page([{ ...w, status: "unavailable", current_price_paisa: null, change_paisa: null, store_url: null }]) });
    render(<MemoryRouter><PriceWatch /></MemoryRouter>);
    expect(await screen.findByText("No longer available")).toBeInTheDocument();
    expect(screen.getByText("Not available")).toBeInTheDocument();
  });

  it("changes the target, loads history, and removes", async () => {
    vi.spyOn(window, "prompt").mockReturnValue("550");
    mockApi({
      "GET /watches": page([w]),
      "PATCH /watches/w1": w,
      "GET /watches/w1/history": { available: true, points: [{ price_paisa: 70000, observed_at: null }, { price_paisa: 65000, observed_at: null }] },
      "DELETE /watches/w1": () => Promise.resolve({ ok: true, status: 204, json: () => Promise.reject(new Error("no body")) }),
    });
    render(<MemoryRouter><PriceWatch /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Change target" }));
    await waitFor(() => {
      const call = global.fetch.mock.calls.find(([, o]) => o?.method === "PATCH");
      expect(JSON.parse(call[1].body)).toEqual({ target_price_paisa: 55000 });
    });
    fireEvent.click(screen.getByRole("button", { name: "Price history" }));
    expect((await screen.findAllByRole("listitem")).length).toBe(2);
    fireEvent.click(screen.getByRole("button", { name: "Stop tracking" }));
    await waitFor(() => expect(global.fetch.mock.calls.some(([, o]) => o?.method === "DELETE")).toBe(true));
  });

  it("says plainly when no history is stored", async () => {
    mockApi({ "GET /watches": page([{ ...w, source: "fairshare" }]), "GET /watches/w1/history": { available: false, points: [] } });
    render(<MemoryRouter><PriceWatch /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Price history" }));
    expect(await screen.findByText(/No price history is stored/)).toBeInTheDocument();
  });
});



describe("already tracked", () => {
  it("a tracked offer shows 'Tracking this price' instead of a button", () => {
    render(<TrackButton item={item} tracked />);
    expect(screen.getByText(/Tracking this price/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Track price" })).toBeNull();
  });

  it("the compare page marks only the offers already tracked", async () => {
    const mk = (id, source, store) => ({ id, source, name: "Rice 5 kg", store_name: store, availability: "in_stock", price_paisa: 70000, currency: "BDT", freshness: "fresh" });
    mockApi({
      "GET /compare/groups/g1": { exact: [mk("e1", "external", "Daraz"), mk("p1", "fairshare", "FairShare")], possible: [], cheapest_id: "e1" },
      "GET /watches/refs": [{ id: "w1", source: "external", product_id: "e1" }],
    });
    const { default: Compare } = await import("../pages/shopper/Compare.jsx");
    const { Route, Routes } = await import("react-router-dom");
    render(
      <MemoryRouter initialEntries={["/app/compare/g1"]}>
        <Routes><Route path="/app/compare/:groupKey" element={<Compare />} /></Routes>
      </MemoryRouter>
    );
    expect(await screen.findByText(/Tracking this price/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Track price" })).toHaveLength(1);
  });

  it("still works when the tracked list cannot be loaded", async () => {
    mockApi({ "GET /watches/refs": () => json({ error: { code: "SERVER_ERROR", message: "x" } }, 500) });
    const { default: useTrackedRefs } = await import("../hooks/useTrackedRefs.js");
    const { renderHook } = await import("@testing-library/react");
    const { result } = renderHook(() => useTrackedRefs());
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(result.current.isTracked({ source: "external", id: "e1" })).toBe(false);
  });
});