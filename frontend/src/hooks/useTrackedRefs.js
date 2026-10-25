import { useCallback, useEffect, useState } from "react";
import { listWatchRefs } from "../api/watches.js";

// Which offers the shopper already tracks. ONE request per page; if it fails the buttons simply behave as before
// (the server still refuses a duplicate). Returns isTracked(item) and markTracked(item) for the button to call.
export default function useTrackedRefs() {
  const [keys, setKeys] = useState(() => new Set());
  useEffect(() => {
    let cancelled = false;
    listWatchRefs()
      .then((refs) => !cancelled && setKeys(new Set(refs.map((r) => `${r.source}:${r.product_id}`))))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);
  const isTracked = useCallback((item) => keys.has(`${item.source}:${item.id}`), [keys]);
  return { isTracked };
}