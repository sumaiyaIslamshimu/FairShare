import { useState } from "react";
import { getVerificationStatus, submitVerification } from "../../api/verification.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate } from "../../utils/format.js";

const TONE = { approved: "green", pending: "amber", rejected: "red", none: "neutral" };
const MAX_BYTES = 5 * 1024 * 1024;

export default function Verification() {
  const { refreshUser } = useAuth();
  const { data, error, loading, reload } = useLoad(getVerificationStatus);
  const [nid, setNid] = useState("");
  const [file, setFile] = useState(null);
  const [formError, setFormError] = useState(null);
  const [busy, setBusy] = useState(false);

  if (loading && !data) return <Loading />;
  const canSubmit = data && (data.status === "none" || data.status === "rejected");

  const onSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    if (!file) return setFormError("Choose a PDF, JPG or PNG document.");
    if (file.size > MAX_BYTES) return setFormError("The document is too large (maximum 5 MB).");
    setBusy(true);
    try {
      await submitVerification(nid, file);
      setNid("");
      setFile(null);
      await reload();
      if (typeof refreshUser === "function") refreshUser();
    } catch (err) {
      setFormError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1>Identity verification</h1>
      <p className="subtitle">
        Needed to list or rent items for rent. A FairShare administrator reviews your document <strong>manually</strong>; there is no automatic check.
      </p>
      <ErrorBox error={error} />
      {data && (
        <Card>
          <p>Status: <Badge tone={TONE[data.status]}>{data.status}</Badge></p>
          {data.submitted_at && <p className="muted">Submitted: {formatDate(data.submitted_at)}</p>}
          {data.status === "pending" && <p>Your document is waiting for review. You will see the result here.</p>}
          {data.status === "approved" && <p>Your identity is verified. Thank you.</p>}
          {data.status === "rejected" && <div className="error-box" role="alert">Rejected: {data.note || "No reason given."} You can submit again below.</div>}
        </Card>
      )}
      {canSubmit && (
        <Card style={{ marginTop: 16 }}>
          <h2>Submit your details</h2>
          <p className="muted">
            Your NID number is stored encrypted and is never shown again, not even to you. The document is kept in a private folder and is opened only by an administrator, and each time it is opened that is recorded.
          </p>
          <form onSubmit={onSubmit}>
            <ErrorBox error={formError} />
            <FormField label="NID number (10, 13 or 17 digits)" id="nid" value={nid} onChange={(e) => setNid(e.target.value)}
                       inputMode="numeric" autoComplete="off" required />
            <FormField label="Document photo or scan (PDF, JPG or PNG, max 5 MB)" id="doc">
              <input id="doc" type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                     onChange={(e) => setFile(e.target.files?.[0] || null)} required />
            </FormField>
            <Button variant="primary" type="submit" disabled={busy}>{busy ? "Uploading…" : "Submit for review"}</Button>
          </form>
        </Card>
      )}
    </>
  );
}