# Setup (Windows + PyCharm)

Requirements: Python 3.12 or newer (the project was planned on 3.12; newer versions may work but are less tested), Node.js 20 or newer, a free MongoDB Atlas account.

## 1. MongoDB Atlas
1. Create a free cluster at https://cloud.mongodb.com.
2. Database Access -> add a database user (username + password).
3. Network Access -> add your current IP address.
4. Connect -> Drivers -> copy the connection string; replace `<password>` with your password.

## 2. Backend (PyCharm Terminal, folder `backend`, `.venv` active)
```
pip install -r requirements.txt
copy .env.example .env
```
Edit `backend\.env` yourself: MONGODB_URI, JWT_SECRET, FERNET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD.
Generate secrets:
```
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Seed and start (always from the `backend` folder, because `.env` is read from there):
```
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```
Check: http://localhost:8000/api/health shows `"database": "up"`; Swagger UI: http://localhost:8000/docs

## 3. Frontend (second Terminal tab, folder `frontend`)
```
npm install
copy .env.example .env
npm run dev
```
Open http://localhost:5173

## 4. Tests
```
cd backend
pytest
cd ..\frontend
npm test
```
Backend tests use an in-memory database (mongomock) and do not touch Atlas.

## Troubleshooting
- `database: down` -> wrong password, IP not allowed in Atlas Network Access, or `<password>` left in the string.
- CORS error in browser -> CORS_ORIGINS in `backend\.env` must contain http://localhost:5173.
- Startup error "field required" -> a value is missing in `backend\.env`.
- PowerShell blocks activation script -> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.