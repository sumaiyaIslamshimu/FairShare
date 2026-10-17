export default function ErrorBox({ error }) {
  if (!error) return null;
  const message = typeof error === "string" ? error : error.message;
  return <div className="error-box" role="alert">{message}</div>;
}