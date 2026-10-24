import { useState } from "react";
import { getScrapingRuns, getScrapingStatus, refreshStore } from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

// The states are shown exactly as the scraper recorded them. "unsupported" is an honest result, not an error.
const TONE = { success: "green", partial: "amber", failure: "red", unsupported: "neutral", never_run: "neutral" };

export default function ScrapingStatus() {
  const status = useLoad(getScrapingStatus);
  const runs = useLoad(() => getScrapingRuns({ page_size: 20 }));
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState(null);
  const [actionError, setActionError] = useState(null);

  const refresh = async (store) => {
    setBusy(store);
    setActionError(null);
    setMessage(null);
    try {
      const r = await refreshStore(store);
      setMessage(`${store}: ${r.status} (${r.items_found} items found)`);
    } catch (e) {
      setActionError(e);
    } finally {
      setBusy(null);
      status.reload();
      runs.reload();
    }
  };

  const columns = [
    { key: "store_name", header: "Store" },
    { key: "status", header: "Status", render: (s) => <><Badge tone={TONE[s.status]}>{s.status}</Badge>{s.stale && <> <Badge tone="amber">stale</Badge></>}</> },
    { key: "configured", header: "Configured", render: (s) => (s.configured ? "yes" : "no") },
    { key: "robots_allowed", header: "robots.txt", render: (s) => (s.robots_allowed === null || s.robots_allowed === undefined ? "Not available" : s.robots_allowed ? "allowed" : "blocked") },
    { key: "last_success_at", header: "Last success", render: (s) => formatDate(s.last_success_at) },
    { key: "items_found", header: "Items" },
    { key: "last_error", header: "Last problem", render: (s) => s.last_error || "—" },
    { key: "actions", header: "", render: (s) => <Button disabled={busy === s.store} onClick={() => refresh(s.store)}>{busy === s.store ? "Running…" : "Refresh"}</Button> },
  ];
  const runColumns = [
    { key: "store", header: "Store" },
    { key: "started_at", header: "Started", render: (r) => formatDate(r.started_at) },
    { key: "status", header: "Result", render: (r) => <Badge tone={TONE[r.status]}>{r.status}</Badge> },
    { key: "items_found", header: "Items" },
    { key: "errors", header: "Problems", render: (r) => (r.errors?.length ? r.errors.slice(0, 2).join("; ") : "—") },
  ];

  return (
    <>
      <h1>Scraping monitor</h1>
      <p className="subtitle">
        Real status of each store. A store that cannot be read lawfully or reliably is shown as unsupported. A refresh runs now and may take a while; a store can be refreshed once a minute.
      </p>
      <ErrorBox error={actionError || status.error || runs.error} />
      {message && <div className="info-box">{message}</div>}
      <Card>{status.loading && !status.data ? <Loading /> : <DataTable columns={columns} rows={status.data?.map((s) => ({ ...s, id: s.store }))} />}</Card>
      <Card style={{ marginTop: 16 }}>
        <h2>Recent runs</h2>
        {runs.loading && !runs.data ? <Loading /> : <DataTable columns={runColumns} rows={runs.data?.items} emptyText="No runs yet." />}
      </Card>
    </>
  );
}