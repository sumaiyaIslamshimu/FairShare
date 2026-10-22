import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useAuth } from "./AuthContext.jsx";
import { addToCart, clearCart, getCart, removeCartItem, updateCartItem } from "../api/cart.js";

const CartContext = createContext(null);

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used inside CartProvider");
  return ctx;
}

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [cart, setCart] = useState({ items: [], total_items: 0, subtotal_paisa: 0 });
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!user || user.role !== "user") return;
    setLoading(true);
    try {
      const data = await getCart();
      setCart(data);
    } catch (err) {
      console.error("Failed to load cart", err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const add = async (productId, qty = 1) => {
    const updated = await addToCart(productId, qty);
    setCart(updated);
  };

  const update = async (productId, qty) => {
    const updated = await updateCartItem(productId, qty);
    setCart(updated);
  };

  const remove = async (productId) => {
    const updated = await removeCartItem(productId);
    setCart(updated);
  };

  const clear = async () => {
    await clearCart();
    setCart({ items: [], total_items: 0, subtotal_paisa: 0 });
  };

  return (
    <CartContext.Provider value={{ cart, loading, add, update, remove, clear, refresh: fetchCart }}>
      {children}
    </CartContext.Provider>
  );
}