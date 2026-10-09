import { Navigate } from "react-router-dom";
import { getSellerSession } from "../../utils/sellerAuth";

// UI-level guard only. The backend must still enforce seller authorization.
export default function SellerRoute({ children }) {
  const session = getSellerSession();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return children;
}