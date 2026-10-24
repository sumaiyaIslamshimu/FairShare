import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { getMyOrders, cancelOrder } from "../../api/cart.js";
import { formatPrice, formatDate } from "../../utils/format.js";
import Button from "../../components/Button.jsx";

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = async () => {
    try {
      const data = await getMyOrders();
      setOrders(data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleCancel = async (id) => {
    if (!window.confirm("Are you sure you want to cancel this order?")) return;
    try {
      await cancelOrder(id);
      fetchOrders();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div>Loading orders...</div>;
  if (!orders.length) return <h2>You have no orders yet.</h2>;

  return (
    <div>
      <h2>My Orders</h2>
      {orders.map((order) => (
        <div key={order.id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
            <h3>Order: {order.order_number}</h3>
            <span style={{ fontWeight: "bold", textTransform: "uppercase" }}>{order.status}</span>
          </div>
          <p>Date: {formatDate(order.created_at)}</p>
          <p>Total: {formatPrice(order.total_paisa, order.currency)}</p>

          <div style={{ marginTop: "1rem", padding: "1rem", background: "#f9f9f9" }}>
            <h4>Items:</h4>
            <ul>
              {order.items.map((item) => (
                <li key={item.id}>
                                    {item.quantity}x {item.title_snapshot} - {formatPrice(item.line_total_paisa, order.currency)} ({item.item_status})
                  {item.item_status === "delivered" && (
                      <> · <Link to={`/app/reviews?item=${item.id}`}>Write a review</Link> · <Link to={`/app/returns?item=${item.id}`}>Return this item</Link></>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <p style={{ marginTop: "10px" }}>
            <Link to={`/app/complaints?type=order&id=${order.id}`}>Report a problem with this order</Link>
          </p>
          {["pending", "confirmed"].includes(order.status) && (
            <Button onClick={() => handleCancel(order.id)} style={{ marginTop: "10px", background: "red" }}>
              Cancel Order
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}