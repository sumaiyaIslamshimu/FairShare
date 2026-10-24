import { decideAdminReturn, listAdminReturns } from "../../api/admin.js";
import ReturnsTable from "../../components/ReturnsTable.jsx";

export default function Returns() {
  return (
    <>
      <h1>Returns</h1>
      <p className="subtitle">All return requests. You can step in when a seller does not respond. Every decision you make is audit-logged. Refunds are simulated.</p>
      <ReturnsTable load={listAdminReturns} decide={decideAdminReturn} />
    </>
  );
}