// The URL prefix of each role's portal.
export const PORTAL_BASE = { user: "/app", seller: "/seller", admin: "/admin" };

// Notifications store a short link such as "orders"; this turns it into this person's real path.
export const portalPath = (role, link) => `${PORTAL_BASE[role] || "/app"}${link ? "/" + link : ""}`;