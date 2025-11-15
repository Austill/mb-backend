# Mind Buddy — Backend

A Flask-based backend for the Mind Buddy mental-wellness app. This repo provides REST endpoints for user authentication, journal and mood tracking, payments, and an AI-powered conversational assistant (Sereni) backed by the Groq LLM API.

This README covers: setup, environment variables, running locally, deployment notes (Render), common troubleshooting (CORS, LLM key), and a quick API reference.

## Table of contents
- Project overview
- Requirements
- Environment variables
- Quick start (Windows PowerShell)
- Running locally
- Tests (basic checks)
- Deployment notes (Render)
- API reference (key endpoints)
- Troubleshooting
- Security & secret handling
- Appendix: .env.example

## Project overview

The backend is a Flask application that exposes a set of REST endpoints under `/api/*`. Key features:
- User registration, login and JWT-based authentication
- Journals and mood entry endpoints
- Payment hooks and subscription handling
- AI chat powered by a Groq LLM (Sereni)
- Sentiment analysis integrations

Project layout (top-level, relevant paths):
- `backend/` — main Flask app
  - `backend/routes/` — route blueprints (auth, chat, ai_chat, journal, mood, payments, subscribe, user, webhook)
  - `backend/services/` — business logic services (LLM, sentiment, chat, payment integrations)
  - `backend/models/` — DB models
  - `backend/config.py` — configuration and environment loading
  - `backend/extensions.py` — Flask extensions (CORS, JWT, Bcrypt)
  - `backend/run.py` — local run entrypoint

## Requirements
- Python 3.10+ (use the version your environment supports)
- pip
- A MongoDB URI (Atlas recommended for production)
- Groq account and API key for AI features (if you plan to use AI chat)

Install dependencies (from repo root):

```powershell
# From the repository root (contains `backend/requirements.txt`)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

## Environment variables
The app reads env vars (via `python-dotenv` in `backend/config.py`). For production, set these in your hosting provider (Render) — do not commit secrets to the repo.

Important variables (add these to Render or a local `.env` during development):

- `SECRET_KEY` — Flask secret for JWT signing and session security.
- `MONGO_URI` — MongoDB connection string (Atlas recommended).
- `MONGODB_DB_NAME` — Name of the DB (default: `mindbuddy`).
- `GROQ_API_KEY` — Groq API key for LLM requests (REPLACE with your key). If not set, the AI endpoints will return a 503 and a helpful log will appear.
- `GROQ_MODEL` — (optional) model name to use (e.g. `llama-3.1-8b-instant`).
- `CORS_ORIGINS` — Comma-separated list of allowed origins for CORS (e.g. `https://mb-frontend-rho.vercel.app,http://localhost:3000`). Must include exact scheme (https://) for deployed frontends.
- `JWT_SECRET_KEY` — (optional) separate key for JWT; otherwise `SECRET_KEY` is used.
- `LOGGING_LEVEL` — DEBUG/INFO/WARNING (default INFO).
- `FLW_*` — Flutterwave payment keys (if you use payments): `FLW_SECRET_KEY`, `FLW_SIGNATURE_KEY`, `FLW_PLAN_ID`.

## Quick start — local development (Windows PowerShell)

1. Create and activate venv, install deps (see earlier code block).
2. Copy `.env.example` to `.env` and fill values (local values fine for dev):

```powershell
cp backend/.env.example backend/.env
# Edit backend/.env with your keys and MONGO_URI
notepad backend/.env
```

3. Run the app locally:

```powershell
# From repository root
python backend/run.py
# App will listen on http://0.0.0.0:5000
```

4. Verify basic health endpoint:

```powershell
curl -i http://localhost:5000/api/health
```

## Running tests / quick checks
This repo includes some lightweight test files (e.g., `test_server.py`). There is no full test harness configured by default. To run a simple server import check you can run:

```powershell
python -c "import backend; print('OK', backend)" 
```

## Deployment notes (Render)
Recommended: use Render's environment variables to set secrets and config. Key points:
- Add `GROQ_API_KEY`, `MONGO_URI`, `SECRET_KEY`, and `CORS_ORIGINS` in the Render service dashboard (Environment > Environment Variables).
- Ensure `CORS_ORIGINS` includes your production frontend URL with https, e.g. `https://mb-frontend-rho.vercel.app`.
- After updating env vars, redeploy or restart the service to pick up changes.

If the AI chat fails with 503 or the logs show `Failed to initialize LLMService`, it usually means `GROQ_API_KEY` is missing or invalid in the Render env.

### Recommended Render env example (single line):
```
GROQ_API_KEY=your_new_groq_key_here
CORS_ORIGINS=https://mb-frontend-rho.vercel.app
MONGO_URI=your_mongo_uri
SECRET_KEY=your_secret_key
LOGGING_LEVEL=INFO
```

## API reference — key endpoints
(Only high level; see `backend/routes/` for full details.)

Auth
- POST /api/auth/register — Register a new user
  - Body JSON: { firstName, lastName, email, password }
- POST /api/auth/login — Login
  - Body JSON: { email, password }
  - Response: { token, user }
- PUT /api/auth/change-password — (auth) Change password

AI Chat (Sereni)
- POST /api/chat/message — (auth) Send user message to AI
  - Body JSON: { message: "...", conversation_id: "optional" }
  - Requires Authorization: Bearer <JWT>
- GET /api/chat/conversations — (auth) Recent conversations
- GET /api/chat/conversation/<id> — (auth) Get a conversation
- GET /api/chat/history — (auth) All messages for user
- GET /api/chat/proactive-check-in — (auth) AI generated check-in

Other
- GET /api/health — Service health
- Various endpoints under `/api/journal`, `/api/user`, `/api/mood`, `/api/payments`, `/api` (subscribe, webhook) — see `backend/routes/` for details

### Example: login + chat (PowerShell curl)
```powershell
# Login to get JWT
$login = curl -s -X POST "https://<your-backend>/api/auth/login" -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"password"}'
# Extract token (quick, using jq would be nicer). If jq installed:
# $token = ($login | jq -r .token)

# Example POST message with token
curl -i -X POST "https://<your-backend>/api/chat/message" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <YOUR_JWT>" `
  -d '{"message":"Hello Sereni, how are you?"}'
```

> Note: the chat endpoint will return 503 if the Groq LLM client fails to initialize. Check server logs for `Failed to initialize LLMService` when diagnosing.

## Troubleshooting

CORS errors
- Symptom: browser console shows "No 'Access-Control-Allow-Origin' header is present" or preflight fails.
- Cause: the `Origin` header from your frontend did not match any entry in `CORS_ORIGINS`.
- Fix: set `CORS_ORIGINS` to include your frontend origin including scheme (e.g. `https://mb-frontend-rho.vercel.app`) in Render environment variables or your server environment. Avoid trailing commas.
- Debug tip: request the health endpoint with an Origin header and inspect headers:
```powershell
curl -i -H "Origin: https://mb-frontend-rho.vercel.app" https://<your-backend>/api/health
```

LLM / AI chat errors
- Symptom: POST `/api/chat/message` returns 500 or 503; logs show errors about Groq key or API.
- Cause: `GROQ_API_KEY` missing, invalid, or client cannot reach Groq.
- Fix: rotate/regenerate GROQ_API_KEY in provider dashboard, set `GROQ_API_KEY` in Render env, redeploy.
- Local check: ensure `backend/.env` (for local dev) contains `GROQ_API_KEY` (do not commit this file).

500 Internal Server Errors
- Check the server logs (Render dashboard logs or local console). The backend logs stack traces for exceptions. Look for `Chat message error` or `Login error` context.

JWT / Authentication
- Make sure you include `Authorization: Bearer <token>` header where endpoints are protected.

## Security & secrets
- DO NOT commit real secrets to git. If a secret was committed, rotate/revoke it immediately.
- To stop tracking a `.env` already committed:
```powershell
git rm --cached backend/.env
git commit -m "Stop tracking backend/.env (contains secrets)"
git push origin main
```
- Ensure `.gitignore` contains `.env` (this project includes .env in `.gitignore`).

## Appendix — recommended `backend/.env.example`
Copy this to `backend/.env` and fill values locally. Never commit actual keys.

```dotenv
# Flask
SECRET_KEY=replace_me_with_a_secret
LOGGING_LEVEL=DEBUG

# Database
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.example.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=mindbuddy

# LLM (Groq)
GROQ_API_KEY=replace_with_groq_key
GROQ_MODEL=llama-3.1-8b-instant

# CORS (comma separated)
CORS_ORIGINS=http://localhost:3000,https://mb-frontend-rho.vercel.app

# JWT
JWT_SECRET_KEY=replace_jwt_secret_if_needed

# Payments (optional)
FLW_SECRET_KEY=
FLW_SIGNATURE_KEY=
FLW_PLAN_ID=
REDIRECT_URL=
```

---

If you'd like, I can:
- Add a small `/api/ai_health` endpoint that returns LLM readiness (available/unavailable).
- Add startup logs that print `CORS_ORIGINS` at boot to make CORS troubleshooting easier.
- Create a `dev-instructions.md` with step-by-step screenshots for deploying to Render and Vercel.

If you want any of those, tell me which and I'll add them next.
