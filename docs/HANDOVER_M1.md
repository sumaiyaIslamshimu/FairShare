# Handover: Member 1 -> Member 2

Fill in the real results yourself. Do not tick a box you did not verify.

## Verified by Member 1
- [ ] Backend starts: `uvicorn app.main:app --reload --port 8000` (from `backend`)
- [ ] `/api/health` shows database "up" against real Atlas
- [ ] `python -m app.db.seed` runs twice with no duplicates (6 categories)
- [ ] `pytest` in `backend` — paste summary line here: ______
- [ ] `npm test` in `frontend` — paste summary line here: ______
- [ ] Frontend starts: `npm run dev`
- [ ] Register + login works in the browser for a shopper, a seller, and the seeded admin
- [ ] A seller sees the "pending approval" notice
- [ ] No password_hash in any response (check Swagger)

## Accepted by Member 2 (re-run everything above on your own machine)
- [ ] Setup worked from docs/SETUP.md alone (note any gaps: ______)
- [ ] Both test suites pass — paste summary: ______

## Interfaces Member 2 may rely on
- `from app.core.deps import get_current_user, require_role, require_approved_seller`
- `from app.services.category_service import validate_category_pair`
- `from app.core.errors import AppError`
- `from app.db.mongo import get_db, to_object_id`
- `from app.models.product import ProductSource, StoreName, Availability, Freshness, CURRENCY`
- Frontend: `api/client.js (request)`, `context/AuthContext.jsx (useAuth)`, shared components, and the marked blocks in `navConfig.js` and `routes.jsx`.

## Known limitations
- Foundation code was written without being executed in the author's sandbox (no network); run the tests first and report any failure.
- Project was planned for Python 3.12 / Node 20; Python 3.14 and Node 24 are untested here.
- JWT is kept in localStorage (XSS trade-off); no refresh tokens or password reset.
- No email verification. No rate limiting on login.
- Admin login page has no "forgot password".
- Scraping, price tracking, rentals, messaging and NID verification are intentionally NOT part of Member 1.