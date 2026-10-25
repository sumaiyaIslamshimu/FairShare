import { useEffect, useState } from "react";
import { getSellerProfile, updateSellerProfile } from "../../api/seller.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import useLoad from "../../hooks/useLoad.js";

const TONE = { approved: "green", pending: "amber", suspended: "red" };

export default function BusinessProfile() {
  const { data, error, loading, reload } = useLoad(getSellerProfile);
  const [form, setForm] = useState({ business_name: "", description: "", contact_phone: "", address: "" });
  const [formError, setFormError] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (data) {
      setForm({
        business_name: data.business_name || "", description: data.description || "",
        contact_phone: data.contact_phone || "", address: data.address || "",
      });
    }
  }, [data]);

  if (loading && !data) return <Loading />;

  const submit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setSaved(false);
    try {
      await updateSellerProfile(form);
      setSaved(true);
      reload();
    } catch (err) {
      setFormError(err);
    }
  };

  return (
    <>
      <h1>Business profile</h1>
      <p className="subtitle">Shoppers see your business name next to your products.</p>
      <ErrorBox error={error} />
      {data && (
        <Card>
          <p>Account status: <Badge tone={TONE[data.status]}>{data.status}</Badge></p>
          {data.status === "pending" && <p className="muted">Your account becomes approved after an administrator verifies your identity. Until then you cannot add products.</p>}
          <form onSubmit={submit}>
            <ErrorBox error={formError} />
            {saved && <div className="info-box">Profile saved.</div>}
            <FormField label="Business name" id="bp-name" required minLength={2} maxLength={120} value={form.business_name} onChange={(e) => setForm({ ...form, business_name: e.target.value })} />
            <FormField label="Contact phone" id="bp-phone" maxLength={20} value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} />
            <FormField label="Address" id="bp-addr" maxLength={300} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            <FormField label="About your business" id="bp-desc">
              <textarea id="bp-desc" className="input" rows={4} maxLength={2000} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </FormField>
            <Button variant="primary" type="submit">Save</Button>
          </form>
        </Card>
      )}
    </>
  );
}