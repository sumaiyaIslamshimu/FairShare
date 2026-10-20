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
    // --- Member 4 ---
  ],
  seller: [
    // --- Member 1 ---
    { to: "/seller", label: "Home", end: true },
    // --- Member 2 ---
    // --- Member 3 ---
    // --- Member 4 ---
  ],
  admin: [
    // --- Member 1 ---
    { to: "/admin", label: "Home", end: true },
    // --- Member 4 ---
  ],
};