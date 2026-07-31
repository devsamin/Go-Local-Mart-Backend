# Local Mart API

Django REST API for products, carts, inventory-safe checkout, Stripe payments,
orders, reviews, offers, and seller analytics.

## Local development

Local development intentionally uses its own SQLite database and local media
directory. It does not share production data.

1. Copy `.env.example` to `.env` and set local values.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Run `python manage.py migrate`.
4. Run `python manage.py runserver`.

On Windows, use the project virtual environment directly:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

The local health endpoint is `http://localhost:8000/api/health/`. A healthy
local response reports `sqlite` and `FileSystemStorage`; both are expected to
show `persistent: false` because they are local development services.

## Production persistence requirements

Render's service filesystem is ephemeral. Production must use:

- PostgreSQL through `DATABASE_URL` for relational data.
- Cloudinary through `CLOUDINARY_URL` (or the three individual Cloudinary
  credential variables) for uploaded images.

The application refuses to start on Render with `DEBUG=True`, SQLite, or
without persistent media credentials. `USE_CLOUDINARY=False` cannot disable
this protection on Render. This prevents successful-looking writes that
disappear on the next deployment, restart, or idle spin-down.

Configure the existing Render service as follows:

```text
Build Command: bash build.sh
Start Command: python manage.py migrate --noinput && gunicorn localmart_backend.wsgi:application
```

Required environment variables:

```text
DATABASE_URL=<Render Postgres internal connection string>
SECRET_KEY=<long random secret>
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
FRONTEND_URL=https://golocalmart.vercel.app
BACKEND_BASE_URL=https://local-mart-11yd.onrender.com
CORS_ALLOWED_ORIGINS=https://golocalmart.vercel.app
CSRF_TRUSTED_ORIGINS=https://golocalmart.vercel.app
STRIPE_SECRET_KEY=<Stripe secret key>
STRIPE_WEBHOOK_SECRET=<Stripe webhook signing secret>
DEBUG=False
```

After deployment, `https://local-mart-11yd.onrender.com/api/health/` must return
HTTP 200 and report:

```json
{
  "database": { "backend": "postgresql", "persistent": true },
  "media": { "backend": "MediaCloudinaryStorage", "persistent": true }
}
```

Use a non-expiring PostgreSQL plan for production. Render's free PostgreSQL
instances expire, so they are suitable only for temporary testing.

## Existing data

The old `db.sqlite3` file is ignored and no longer tracked. It remains available
on each developer's machine for local work, but deployment must not use it.
Create the PostgreSQL database and migrate any recoverable SQLite data before
accepting new production writes. Records already lost during an ephemeral
filesystem reset cannot be recovered without an external backup.

## Verification

```text
python manage.py check --deploy
python manage.py test
python manage.py makemigrations --check --dry-run
```

Stripe browser redirects never mark an order paid. Only the verified Stripe
webhook or a server-to-server Checkout Session verification can do that. The
webhook endpoint is `/api/payment/stripe/webhook/`. Register that HTTPS endpoint
in Stripe for `checkout.session.completed`,
`checkout.session.async_payment_succeeded`, `checkout.session.expired`, and
`checkout.session.async_payment_failed`, then copy its signing secret to
`STRIPE_WEBHOOK_SECRET`.
