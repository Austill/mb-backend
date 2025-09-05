# Security guidelines for Mind Buddy backend (summary)

- Password storage: use bcrypt (already implemented). Ensure `bcrypt.generate_password_hash` is used and never store plaintext passwords.
- Secret management: keep `Config.SECRET_KEY` out of repository and set via environment variable. Do **not** use the default secret in production.
- Token policy: JWT tokens are signed with HS256. Use short-ish expiry (e.g., 1h) for access tokens and refresh tokens if needed.
- Rate limiting: add rate limits on auth endpoints (login/register) to prevent brute force.
- Input validation: validate and sanitize inputs at the API boundary (especially registration and journal content).
- Database rules:
  - Use proper foreign keys (already present), and ensure rows are queried by `user_id` to avoid leaking other users' data.
  - Migrate schema with Alembic for controlled changes (migrations/ present).
- Transport: enforce HTTPS in production; configure CORS only for known origins.
- Logging: avoid logging sensitive data (passwords, tokens).
- Session policy: on logout, delete token client-side and optionally implement server-side token blacklist if needed.
