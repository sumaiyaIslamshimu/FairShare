# FairShare Architecture (condensed)

**Stack:** React + Vite (frontend), FastAPI (backend), MongoDB Atlas.

## Layers (backend, MVC-style)
`routers/` (HTTP only = controllers) -> `services/` (business rules) -> MongoDB via `db/mongo.py`.
Pydantic models in `models/` validate all input. Auth/role checks live in `core/deps.py`.
React pages are the view.

## Frontend
One SPA. Route groups: Public, Shopper (`/app`), Seller (`/seller`), Admin (`/admin`).
All HTTP goes through `src/api/client.js`. Route guards are UX only; the backend enforces permissions.

## Module boundaries (the key rule)
| Concern | Collections | API prefix |
|---|---|---|
| External comparison (scraped, comparison-only) | external_products, price_observations, product_matches, scrape_sources, scrape_runs | /api/compare |
| FairShare seller commerce | seller_products, promotions, carts, orders, order_items, messages | /api/seller-products, /api/cart, /api/orders |
| Rentals (isolated) | rental_listings, rental_requests, rental_bookings, rental_events, rental_messages | /api/rentals |
| Admin | uses all, plus audit_logs | /api/admin |

- The cart accepts only a `seller_product_id` and resolves it in `seller_products` only.
- External products have no stock, cart, or edit paths. They link to the original store.
- No shopping query touches rental collections, and rentals never touch shopping collections.

## Roles
`user`, `seller`, `admin`. Admin accounts are created only by `python -m app.db.seed` (from `.env`).
A seller starts with a `pending` seller profile; an admin must approve it before listings can be published.
The role used for authorization is read from the database on every request, not trusted from the token.

## Decisions
Synchronous PyMongo + mongomock for tests. Money as integer paisa (BDT x 100). Simulated payment only.
Manual NID verification (no government integration). JWT stored in browser localStorage (documented XSS trade-off for this MVP).