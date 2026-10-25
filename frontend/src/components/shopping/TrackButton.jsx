import { useState } from "react";
import { addWatch } from "../../api/watches.js";
import Button from "../Button.jsx";

// "Track price" for one offer. Asks for an optional target (in Taka) and creates the watch.
// It only sends a request when clicked, so listing many offers does not make many requests.
export default function TrackButton({ item, tracked = false }) {
  const [state, setState] = useState("idle");
  const [message, setMessage] = useState("");

if (tracked && state !== "done") {
  return <span className="muted">✓ Tracking this price</span>;
}

  const click = async () => {
    const answer = window.prompt(
      `Tell me when the price of "${item.name}" falls to this amount in Taka. Leave empty to be told about any price drop.`,
      ""
    );
    if (answer === null) return;
    const text = answer.trim();
    const body = { source: item.source, product_id: item.id };
    if (text) {
      const taka = Number(text);
      if (!(taka > 0)) return setMessage("Enter a number above 0.");
      body.target_price_paisa = Math.round(taka * 100);
    }
    setState("busy");
    setMessage("");
    try {
      await addWatch(body);
      setState("done");
    } catch (e) {
      setState(e.code === "ALREADY_WATCHING" ? "done" : "idle");
      setMessage(e.code === "ALREADY_WATCHING" ? "" : e.message);
    }
  };

  if (state === "done") return <span className="muted">✓ Tracking this price</span>;
  return (
    <span>
      <Button type="button" onClick={click} disabled={state === "busy"}>Track price</Button>
      {message && <small role="alert" className="muted"> {message}</small>}
    </span>
  );
}