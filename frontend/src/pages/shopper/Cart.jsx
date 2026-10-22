import { useNavigate } from "react-router-dom";
import { useCart } from "../../context/CartContext.jsx";
import { formatPrice } from "../../utils/format.js";
import Button from "../../components/Button.jsx";

export default function Cart() {
  const { cart, loading, update, remove } = useCart();
  const navigate = useNavigate();

  if (loading) return <div>Loading cart...</div>;
  if (!cart?.items?.length) return <h2>Your cart is empty.</h2>;

  return (
    <div className="cart-page">
      <h2>Shopping Cart</h2>
      <div className="cart-items">
        {cart.items.map((item) => (
          <div key={item.seller_product_id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem", display: "flex", justifyContent: "space-between" }}>
            <div>
              <h3>{item.title}</h3>
              <p>Seller: {item.seller_name || item.seller_id}</p>
              <p>
                Price: {formatPrice(item.effective_price_paisa, item.currency)}
                {item.discount_percent > 0 && (
                  <span style={{ color: "green", marginLeft: "10px" }}>
                    ({item.discount_percent}% OFF!)
                  </span>
                )}
              </p>
              <div style={{ marginTop: "10px" }}>
                <label>Qty: </label>
                <input
                  type="number"
                  min="1"
                  max={item.stock_qty}
                  value={item.quantity}
                  onChange={(e) => update(item.seller_product_id, parseInt(e.target.value, 10))}
                  style={{ width: "60px", marginRight: "10px" }}
                />
                <Button onClick={() => remove(item.seller_product_id)}>Remove</Button>
              </div>
            </div>
            <div style={{ textAlign: "right", fontWeight: "bold" }}>
              Total: {formatPrice(item.line_total_paisa, item.currency)}
            </div>
          </div>
        ))}
      </div>

      <div style={{ textAlign: "right", marginTop: "2rem", padding: "1rem", background: "#f9f9f9" }}>
        <h3>Subtotal: {formatPrice(cart.subtotal_paisa, cart.currency)}</h3>
        <Button onClick={() => navigate("/app/checkout")} style={{ marginTop: "10px", padding: "10px 20px" }}>
          Proceed to Checkout
        </Button>
      </div>
    </div>
  );
}