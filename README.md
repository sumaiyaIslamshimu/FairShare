# FairShare

FairShare is a product-discovery app with a React/Vite frontend and a FastAPI backend backed by MongoDB.

## Run locally

1. Set `MONGO_URI` in `backend/.env`.
2. Start the API from the `backend` directory:

   ```powershell
   ..\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

3. In another terminal, start the frontend from the `frontend` directory:

   ```powershell
   npm install
   npm run dev
   ```

   Vite proxies `/api` requests to `http://127.0.0.1:8000`, so product search uses the running backend without hard-coded browser URLs.

## Product search

The `GET /products/search` endpoint supports `q`, `min_price`, `max_price`, comma-separated `category` selections, `rating_min`, and `sort` query parameters.

To load the example products, run `..\.venv\Scripts\python.exe seed_data.py` from `backend`. **This seed script replaces the documents in the `fairshare.products` collection**, so only run it against a database whose product data you intend to overwrite.
