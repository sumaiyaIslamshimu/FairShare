# Database Schema (all collections)

Conventions: `_id` ObjectId (exposed as `id`); `created_at`/`updated_at` UTC; money in integer paisa; category links use slugs.
Created by Member 1 now: users, seller_profiles, categories, subcategories. The rest are defined here so later members agree on field names.

## Member 1
**users** — email (unique, lowercase), full_name, phone, password_hash, role (user|seller|admin), is_active, verification_status (none|pending|approved|rejected), created_at, updated_at.
**seller_profiles** — user_id (unique), business_name, description, contact_phone, address, status (pending|approved|rejected|suspended), created_at, updated_at.
**categories** — slug (unique), name, is_active, order.
**subcategories** — slug (unique), category_slug (indexed), name, is_active.

## Member 2
**seller_products** — seller_id, title, description, brand, category_slug, subcategory_slug, price_paisa (>0), currency, stock_qty (>=0), status (active|inactive|removed), moderation_status (visible|hidden), images[], unit, attributes{}, source="fairshare". Indexes: seller_id, (category_slug, subcategory_slug), text(title, brand).
**external_products** — store (daraz|pickaboo|chaldal|shwapno|agora|rokomari), store_product_id, name, brand, model, price_paisa, currency, image_url, product_url (required), category_slug, subcategory_slug, specs{}, quantity, unit, package_size, availability, normalized_key, first_seen_at, last_seen_at, last_successful_at, freshness (fresh|stale|unavailable), source="external". Unique (store, store_product_id). NO stock/cart fields.
**price_observations** — external_product_id, price_paisa, availability, observed_at (append-only).
**product_matches** — group_key (unique), external_product_ids[], seller_product_ids[], match_type (exact|possible), reasons[], differences[].
**scrape_sources** — store (unique), status (success|partial|failure|unsupported|never_run), last_attempt_at, last_success_at, last_error, items_found, robots_allowed, notes.
**scrape_runs** — store, started_at, finished_at, status, items_found, errors[].

## Member 3
**promotions** (contract used by Member 2's `effective_price`) — seller_id, product_ids[] (seller_products ids), discount_percent (1-90), starts_at, ends_at, is_active. Effective price = price_paisa reduced by the largest active promotion covering now; computed server-side only.
**carts** — user_id (unique), items[{seller_product_id, quantity}]. No prices stored.
**orders** — user_id, order_number, status (pending|confirmed|shipped|delivered|cancelled), subtotal_paisa, total_paisa, payment{mode:"simulated", status}, shipping_address, created_at.
**order_items** — order_id, seller_id, seller_product_id, title_snapshot, unit_price_paisa, quantity, item_status.
**messages** — thread participants (customer_id, seller_id), order_id|product_id (optional), sender_id, body, read, created_at.
**rental_listings** — owner_id, title, description, daily_rate_paisa, deposit_paisa, location, images[], status, available_from, available_to. Uses NO shopping taxonomy.
**rental_requests** — listing_id, renter_id, start_date, end_date, status (pending|accepted|rejected|cancelled).
**rental_bookings** — request_id, listing_id, owner_id, renter_id, start_date, end_date, status (confirmed|active|completed|cancelled).
**rental_events** — booking_id|request_id, event, actor_id, at.
**rental_messages** — request_id, sender_id, body, created_at.

## Member 4
**verification_records** — user_id (unique), nid_encrypted (Fernet), nid_last4, doc_path (private, random filename), status, reviewed_by, reviewed_at, note. NEVER returned by ordinary APIs.
**complaints** — filer_id, target_type (order|seller|rental), target_id, description, status (open|in_review|resolved|dismissed), admin_note.
**audit_logs** — actor_id, action, target, at (admin actions and every document access).

## Sensitive data
Stored: encrypted NID, last 4 digits, one private document path. Never stored/logged: plaintext passwords, raw NID in logs. Files live in `private_uploads/` (git-ignored, never served statically).