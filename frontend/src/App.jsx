import AppRoutes from "./routes.jsx";
import { CartProvider } from "./context/CartContext.jsx";

export default function App() {
  return (
    <CartProvider>
      <AppRoutes />
    </CartProvider>
  );
}