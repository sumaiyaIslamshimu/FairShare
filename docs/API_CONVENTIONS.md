# API Conventions

- Base path: `/api`. Swagger UI: `/docs`.
- Auth header: `Authorization: Bearer <JWT>`.
- JSON field names: `snake_case`. IDs are strings exposed as `id`.
- Money: integer paisa in fields ending `_paisa`; currency `BDT`.
- Dates: ISO 8601 UTC.
- Pagination: `?page=1&page_size=20` -> `{ "items": [...], "total": n, "page": 1, "page_size": 20 }`.

## Error format (always)
```json
{ "error": { "code": "EMAIL_EXISTS", "message": "Human readable text.", "details": null } }
```
| Status | Meaning |
|---|---|
| 400 | Bad request logic (e.g. NOT_A_FAIRSHARE_PRODUCT) |
| 401 | Not logged in / invalid token |
| 403 | Logged in but not allowed (role, ownership, approval) |
| 404 | Not found (also used to hide other users' records) |
| 409 | Conflict (duplicate email, out of stock, date overlap) |
| 422 | Validation error (`VALIDATION_ERROR` with field list, or `INVALID_CATEGORY`) |

## Foundation endpoints (Member 1)
| Method | Route | Role | Notes |
|---|---|---|---|
| GET | /api/health | public | `{status, database}` |
| POST | /api/auth/register | public | role `user` or `seller` only; seller needs `business_name` |
| POST | /api/auth/login | public | returns `{access_token, token_type, user}` |
| GET | /api/auth/me | any logged in | user + `seller_status` for sellers |
| GET | /api/categories | public | nested categories/subcategories (active only) |

## Rules for everyone
Validate server-side. Never trust client price/ownership. Use `require_role` / `require_approved_seller`.
Validate categories with `category_service.validate_category_pair`.