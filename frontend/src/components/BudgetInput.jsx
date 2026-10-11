import { useState, useEffect } from "react";
import { useBudget } from "../hooks/useBudget";
import "./BudgetInput.css";

function BudgetInput() {
  const { budget, setBudget, clearBudget } = useBudget();
  const [inputValue, setInputValue] = useState(budget ?? "");
  const [error, setError] = useState("");

  useEffect(() => {
    setInputValue(budget ?? "");
  }, [budget]);

  const handleChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleBlurOrSubmit = () => {
    if (inputValue === "") {
      setError("");
      return;
    }

    const num = Number(inputValue);

    if (Number.isNaN(num) || inputValue.trim() === "") {
      setError("Enter a valid number.");
      return;
    }

    if (num <= 0) {
      setError("Budget must be greater than zero.");
      return;
    }

    setError("");
    setBudget(num);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.target.blur();
    }
  };

  const handleClear = () => {
    setInputValue("");
    setError("");
    clearBudget();
  };

  return (
    <div className="budget-widget">
      <label htmlFor="budget-input">My Budget</label>

      <div className="budget-input-row">
        <span className="currency-prefix">$</span>

        <input
          id="budget-input"
          type="text"
          inputMode="decimal"
          placeholder="e.g. 300"
          value={inputValue}
          onChange={handleChange}
          onBlur={handleBlurOrSubmit}
          onKeyDown={handleKeyDown}
        />

        {inputValue !== "" && (
          <button
            type="button"
            className="budget-clear-btn"
            onClick={handleClear}
            aria-label="Clear budget"
          >
            ✕
          </button>
        )}
      </div>

      {error && <p className="field-error">{error}</p>}
    </div>
  );
}

export default BudgetInput;