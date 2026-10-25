import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fileComplaint, listMyComplaints } from "../../api/complaints.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const TONE = { open: "red", in_review: "amber", resolved: "green", dismissed: "neutral" };
const HINT = {
  order: "The order id (shown on your orders page).",
  seller: "The seller's account id.",
  rental: "The rental request id (shown on your rentals page).",
};

export default function MyComplaints() {
  const [params] = useSearchParams(); // lets other pages link here with ?type=order&id=...
  const [form, setForm] = useState({
    target_type: params.get("type") || "order", target_id: params.get("id") || "", description: "",
  });
  const [formError, setFormError] = useState(null);
  const [sent, setSent] = useState(false);
  const { data, error, loading, reload } = useLoad(() => listMyComplaints());

  const submit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setSent(false);
    try {
      await fileComplaint({ ...form, target_id: form.target_id.trim() });
      setForm({ ...form, description: "" });
      setSent(true);
      reload();
    } catch (err) {
      setFormError(err);
    }
  };

  const columns = [
    { key: "created_at", header: "Filed", render: (c) => formatDate(c.created_at) },
    { key: "target_type", header: "About" },
    { key: "description", header: "What you told us" },
    { key: "status", header: "Status", render: (c) => <Badge tone={TONE[c.status]}>{c.status}</Badge> },
    { key: "admin_note", header: "Reply", render: (c) => c.admin_note || "—" },
  ];

  return (
    <>
      <h1>Complaints</h1>
      <p className="subtitle">Tell us about a problem with an order, a seller or a rental. An administrator will review it.</p>
      <Card>
        <h2>File a complaint</h2>
        <form onSubmit={submit}>
          <ErrorBox error={formError} />
          {sent && <div className="info-box">Your complaint was sent.</div>}
          <FormField label="About" id="c-type">
            <select id="c-type" className="input" value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value })}>
              <option value="order">An order</option>
              <option value="seller">A seller</option>
              <option value="rental">A rental</option>
            </select>
          </FormField>
          <FormField label={`Id — ${HINT[form.target_type]}`} id="c-id" value={form.target_id} required
                     onChange={(e) => setForm({ ...form, target_id: e.target.value })} />
          <FormField label="What happened? (at least 10 characters)" id="c-desc">
            <textarea id="c-desc" className="input" rows={4} minLength={10} maxLength={2000} required value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </FormField>
          <Button variant="primary" type="submit">Send complaint</Button>
        </form>
      </Card>
      <Card style={{ marginTop: 16 }}>
        <h2>Your complaints</h2>
        <ErrorBox error={error} />
        {loading && !data ? <Loading /> : <DataTable columns={columns} rows={data?.items} emptyText="You have not filed any complaints." />}
      </Card>
    </>
  );
}