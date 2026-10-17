// A labeled input with an optional error message. Extra props go to the <input>.
export default function FormField({ label, id, error, children, ...inputProps }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children || <input id={id} className="input" {...inputProps} />}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}