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
    { to: "/app/verification", label: "Verification" },
    { to: "/app/complaints", label: "Complaints" },
    { to: "/app/reviews", label: "My Reviews" },
    { to: "/app/returns", label: "My Returns" },
    { to: "/app/pricewatch", label: "Price Watch" },
    { to: "/app/notifications", label: "Notifications" },
  ],
  seller: [
    // --- Member 1 ---
    { to: "/seller", label: "Home", end: true },
    // --- Member 2 ---
    { to: "/seller/products", label: "My Products" },
    { to: "/seller/profile", label: "Business Profile" },
    // --- Member 3 ---
    { to: "/seller/insights", label: "Insights" },
    { to: "/seller/promotions", label: "Promotions" },
    { to: "/seller/orders", label: "Orders" },
    { to: "/seller/rentals", label: "My Rentals" },
    { to: "/seller/messages", label: "Messages" },
    // --- Member 4 ---
    { to: "/seller/verification", label: "Verification" },
    { to: "/seller/complaints", label: "Complaints" },
    { to: "/seller/reviews", label: "Reviews" },
    { to: "/seller/returns", label: "Returns" },
    { to: "/seller/notifications", label: "Notifications" },
  ],
  admin: [
    // --- Member 1 ---
    { to: "/admin", label: "Dashboard", end: true },
    // --- Member 4 ---
    { to: "/admin/users", label: "Users" },
    { to: "/admin/verification", label: "Verification & Sellers" },
    { to: "/admin/listings", label: "Listing Moderation" },
    { to: "/admin/categories", label: "Categories" },
    { to: "/admin/complaints", label: "Complaints" },
    { to: "/admin/scraping", label: "Scraping Monitor" },
    { to: "/admin/audit", label: "Audit Log" },
    { to: "/admin/reviews", label: "Review Moderation" },
    { to: "/admin/returns", label: "Returns" },
    { to: "/admin/notifications", label: "Notifications" },
  ],
};