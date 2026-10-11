import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./TrackProductForm.css";

function isLoggedIn() {
  return !!localStorage.getItem("fairshare_token");
}

function TrackProductForm({ productId, currentLowestPrice }) {
  const navigate = useNavigate();

  const [isOpen, setIsOpen] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [targetPrice, setTargetPrice] = useState(currentLowestPrice);
  const [saving, setSaving] = useState(false);
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");

  const handleButtonClick = () => {
    if (!isLoggedIn()) {
      navigate("/shopper/login");
      return;
    }

    setError("");
    setIsOpen(true);
  };

  const handleSave = async () => {
    setError("");

    if (!targetPrice || Number(targetPrice) <= 0) {
      setError("Enter a valid target price.");
      return;
    }

    setSaving(true);

    try {
      // Placeholder until the backend price-alert endpoint is ready.
      await new Promise((resolve) => setTimeout(resolve, 500));

      console.log("Tracking product:", {
        productId,
        targetPrice: Number(targetPrice),
      });

      setConfirmation(
        "You'll be notified when the price drops to your target."
      );

      setIsTracking(true);
      setIsOpen(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="track-widget">
      <button
        className={`btn-primary track-btn ${isTracking ? "tracking" : ""}`}
        onClick={handleButtonClick}
        disabled={isTracking}
      >
        {isTracking ? "✓ Tracking" : "📈 Track this product"}
      </button>

      {confirmation && !isOpen && (
        <p className="track-confirmation">{confirmation}</p>
      )}

      {isOpen && (
        <div className="track-form-card">
          <label htmlFor="targetPrice">Target Price</label>

          <div className="track-input-row">
            <span className="currency-prefix">৳</span>

            <input
              id="targetPrice"
              type="number"
              min="1"
              step="1"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
            />
          </div>

          {error && <p className="field-error">{error}</p>}

          <div className="track-form-actions">
            <button
              className="btn-secondary"
              onClick={() => {
                setIsOpen(false);
                setError("");
              }}
            >
              Cancel
            </button>

            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default TrackProductForm;