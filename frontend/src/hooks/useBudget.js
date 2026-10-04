import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "fairshare_budget";

export function useBudget() {
  const [budget, setBudgetState] = useState(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    return stored ? Number(stored) : null;
  });

  useEffect(() => {
    const handleStorage = () => {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      setBudgetState(stored ? Number(stored) : null);
    };

    window.addEventListener("storage", handleStorage);

    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const setBudget = useCallback((value) => {
    sessionStorage.setItem(STORAGE_KEY, String(value));
    setBudgetState(value);
  }, []);

  const clearBudget = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY);
    setBudgetState(null);
  }, []);

  return { budget, setBudget, clearBudget };
}