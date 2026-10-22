import { useEffect, useState } from "react";
import { getSellerOrders, updateOrderStatus } from "../../api/seller.js";
import { formatPrice, formatDate } from "../../utils/format.js";

export default function SellerOrders() {
  const [orderItems, setOrderItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = async () => {
    try {
      const data = await getSellerOrders();
      setOrderItems(data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleStatusUpdate = async (id, newStatus) => {
    try {
      await updateOrderStatus(id, newStatus);
      fetchOrders();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div>Loading orders...</div>;
  if (!orderItems.length) return <h2>You have no order items yet.</h2>;

  return (
    <div>
      <h2>Fulfillment Dashboard</h2>
      <p style={{ marginBottom: "2rem", color: "#555" }}>
        Update the fulfillment status of items ordered from your store.
      </p>

      {orderItems.map((item) => (
        <div key={item.id} style={{ border: "1px solid #ddd", padding: "1rem", marginBottom: "1rem", borderRadius: "5px" }}>
          <h3>{item.title_snapshot}</h3>
          <p>Quantity: {item.quantity} | Total: {formatPrice(item.line_total_paisa, "BDT")}</p>

          <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "15px" }}>
            <strong style={{ textTransform: "uppercase" }}>Current Status: {item.item_status}</strong>

            {item.item_status === "confirmed" && (
              <button onClick={() => handleStatusUpdate(item.id, "shipped")} style={{ padding: "5px 15px", background: "#3b82f6", color: "white", border: "none", borderRadius: "3px", cursor: "pointer" }}>
                Mark as Shipped
              </button>
            )}

            {item.item_status === "shipped" && (
              <button onClick={() => handleStatusUpdate(item.id, "delivered")} style={{ padding: "5px 15px", background: "#10b981", color: "white", border: "none", borderRadius: "3px", cursor: "pointer" }}>
                Mark as Delivered
              </button>
            )}

            {item.item_status === "delivered" && (
              <span style={{ color: "green", fontWeight: "bold" }}>✓ Delivered</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}