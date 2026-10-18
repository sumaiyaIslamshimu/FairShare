import { Link } from "react-router-dom";

// variant: "primary" | "outline". Pass `to` to render a router link instead of a button.
export default function Button({ variant = "outline", block = false, to, children, className = "", ...rest }) {
  const cls = `btn ${variant === "primary" ? "btn-primary" : ""} ${block ? "btn-block" : ""} ${className}`.trim();
  if (to) {
    return (
      <Link to={to} className={cls} {...rest}>
        {children}
      </Link>
    );
  }
  return (
    <button className={cls} {...rest}>
      {children}
    </button>
  );
}