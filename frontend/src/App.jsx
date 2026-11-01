import AppRoutes from "./routes.jsx";
import { CartProvider } from "./context/CartContext.jsx";
import GlobalBackground from "./components/GlobalBackground.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";

export default function App() {
  return (
    <CartProvider>
      <GlobalBackground />
      <AppRoutes />
      <ThemeToggle />
    </CartProvider>
  );
}