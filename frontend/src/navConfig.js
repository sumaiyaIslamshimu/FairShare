// Sidebar items per role. Each member appends ONLY inside their own block (final edit: Member 4).
// Only add an item when its page exists — no dead links.

export const HOME_PATH = { user: "/app", seller: "/seller", admin: "/admin" };

export const NAV = {
  user: [
    // --- Member 1 ---
    { to: "/app", label: "Home", end: true },
    // --- Member 2 ---
    { to: "/app/search", label: "Search & Compare" },
    // --- Member 3 ---
    { to: "/app/cart", label: "Cart" },
    { to: "/app/orders", label: "My Orders" },
    { to: "/app/rentals", label: "Rentals" },
    { to: "/app/messages", label: "Messages" },
    // --- Member 4 ---
  ],
  seller: [
    // --- Member 1 ---
    { to: "/seller", label: "Home", end: true },
    // --- Member 2 ---
    // --- Member 3 ---
    { to: "/seller/insights", label: "Insights" },       // <-- ADD THIS
    { to: "/seller/promotions", label: "Promotions" },
    { to: "/seller/orders", label: "Orders" },
    { to: "/seller/rentals", label: "My Rentals" },
    { to: "/seller/messages", label: "Messages" },
    // --- Member 4 ---
  ],
  admin: [
    // --- Member 1 ---
    { to: "/admin", label: "Home", end: true },
    // --- Member 4 ---
  ],
};