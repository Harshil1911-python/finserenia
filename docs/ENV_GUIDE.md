# Serenia Accounting — Environment Variable Guide

All variables are read via `python-decouple` (`config(...)`) in
`backend/config/settings/production.py`. Copy `.env.example` to `.env`
and fill in real values. **Never commit `.env`.**

## Django Core

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | **Yes** | — | Django cryptographic signing key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. Must be identical across `api`, `celery`, and `celery_beat` processes. |
| `DEBUG` | No | `False` | Set `True` only for local development. |
| `ALLOWED_HOSTS` | **Yes** | — | Comma-separated hostnames, e.g. `localhost,127.0.0.1,api.serenia.app`. |
| `DJANGO_SETTINGS_MODULE` | No | `config.settings.production` | Use `config.settings.development` locally. |

## Database (PostgreSQL)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | **Yes** | Format: `postgresql://USER:PASSWORD@HOST:5432/DBNAME`. On Render, use the auto-injected internal connection string. |

## Redis

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDIS_URL` | **Yes** | `redis://localhost:6379/0` | Used for cache + sessions. |
| `CELERY_BROKER_URL` | **Yes** | `redis://localhost:6379/1` | Celery task queue. Use a **different DB index** than `REDIS_URL`. |
| `CELERY_RESULT_BACKEND` | No | `redis://localhost:6379/2` | Stores task results. |

## JWT

| Variable | Default | Description |
|---|---|---|
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | Access token validity. |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Refresh token validity; rotated + blacklisted on use/logout. |

## CORS

| Variable | Required | Description |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | **Yes** | Comma-separated frontend origins, e.g. `https://app.serenia.com`. No trailing slashes. Must include scheme. |

## Email / SMTP

| Variable | Default | Description |
|---|---|---|
| `EMAIL_HOST` | `smtp.sendgrid.net` | Any SMTP provider works (SES, Mailgun, Postmark, etc.) |
| `EMAIL_PORT` | `587` | |
| `EMAIL_USE_TLS` | `True` | |
| `EMAIL_HOST_USER` | — | For SendGrid, literally the string `apikey`. |
| `EMAIL_HOST_PASSWORD` | — | Your SMTP API key/password. |
| `DEFAULT_FROM_EMAIL` | `noreply@serenia.app` | |

In `config.settings.development`, the email backend is overridden to
`console` — emails print to stdout instead of sending.

## AWS S3 (Optional Media Storage)

| Variable | Default | Description |
|---|---|---|
| `USE_S3` | `False` | Set `True` to store uploaded media (logos, avatars, attachments) on S3 instead of local disk. **Strongly recommended for Render** (ephemeral filesystem). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | — | IAM credentials with S3 read/write to the bucket. |
| `AWS_STORAGE_BUCKET_NAME` | `serenia-media` | |
| `AWS_S3_REGION_NAME` | `ap-south-1` | |

## Security

| Variable | Default | Description |
|---|---|---|
| `SECURE_SSL_REDIRECT` | `True` | Redirects HTTP → HTTPS. Set `False` for local HTTP dev (handled automatically in `development.py`). |
| `SESSION_COOKIE_SECURE` | `True` | Cookies only sent over HTTPS. |
| `CSRF_COOKIE_SECURE` | `True` | |

## Application Branding (initial seed values)

These seed the `system_settings` table on first `seed_initial_data` run.
After seeding, change branding via **Developer Mode → Branding** in the
UI (stored in DB, not env vars).

| Variable | Default |
|---|---|
| `APP_NAME` | `Serenia Accounting` |
| `APP_TAGLINE` | `Smart Cloud ERP for Modern Businesses` |
| `APP_VERSION` | `1.0.0` |
| `APP_URL` | — |

## Localization / Tax Defaults

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_TAX_COUNTRY` | `IN` | Currently India-specific GST/TDS logic. |
| `DEFAULT_CURRENCY` | `INR` | Default company currency on creation. |
| `DEFAULT_DATE_FORMAT` | `%d/%m/%Y` | |

## Super Admin Seed

| Variable | Default | Description |
|---|---|---|
| `SUPERADMIN_EMAIL` | `superadmin@serenia.app` | Created by `seed_initial_data` if no user with this email exists. |
| `SUPERADMIN_PASSWORD` | `Serenia@2024` | **Change immediately after first login.** |
| `SUPERADMIN_NAME` | `Super Administrator` | Split on first space into first/last name. |

## Feature Flags (initial seed values)

These seed `system_settings` (category=`features`). Toggle afterwards
via **Developer Mode → Feature Toggles**.

| Variable | Default |
|---|---|
| `ENABLE_AUDIT_MODULE` | `True` |
| `ENABLE_PAYROLL_MODULE` | `True` |
| `ENABLE_INVENTORY_MODULE` | `True` |
| `ENABLE_BANKING_MODULE` | `True` |
| `ENABLE_TAXATION_MODULE` | `True` |
| `ENABLE_COMPLIANCE_MODULE` | `True` |
| `ENABLE_DEVELOPER_MODE` | `True` |

## Frontend (build-time)

Set in `docker-compose.yml` / `render.yaml`, not `.env`:

| Variable | Description |
|---|---|
| `REACT_APP_API_URL` | Base URL of the Django API, e.g. `https://api.serenia.app/api/v1`. Baked into the build — changing it requires a rebuild. |
