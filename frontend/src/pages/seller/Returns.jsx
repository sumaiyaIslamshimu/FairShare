import { decideSellerReturn, listSellerReturns } from "../../api/returns.js";
import ReturnsTable from "../../components/ReturnsTable.jsx";

export default function Returns() {
  return (
    <>
      <h1>Return requests</h1>
      <p className="subtitle">
        Approve or reject return requests for items you delivered. After you approve and the item is back, choose “Mark received &amp; restock”. Refunds are simulated; no money moves.
      </p>
      <ReturnsTable load={listSellerReturns} decide={decideSellerReturn} />
    </>
  );
}