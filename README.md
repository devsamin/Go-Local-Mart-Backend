# Local Mart API

Django REST API for products, carts, inventory-safe checkout, Stripe payments,
orders, reviews, offers, and seller analytics.

## Local development

With `DJANGO_DEBUG=True` (the Django `DEBUG` setting), local development always
uses its own SQLite database and local media directory. Production credentials
may remain in `.env`; they are ignored locally, so development does not share
production data. The dedicated name avoids collisions with unrelated system
variables named `DEBUG`.

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

- Neon PostgreSQL through its pooled `DATABASE_URL` for relational data.
- Cloudinary through `CLOUDINARY_URL` (or the three individual Cloudinary
  credential variables) for uploaded images.

Storage and database selection follow Django's `DEBUG` setting automatically.
Set `DJANGO_DEBUG=False` in production; the application then requires PostgreSQL
and Cloudinary credentials and refuses to start with SQLite or local upload
storage. Render always forces debug mode off, even if a stale dashboard variable
is set to true.

Configure the existing Render service as follows:

```text
Build Command: bash build.sh
Start Command: python manage.py migrate --noinput && gunicorn localmart_backend.wsgi:application
```

Required environment variables:

```text
DATABASE_URL=<Neon pooled PostgreSQL connection string>
SECRET_KEY=<long random secret>
CLOUDINARY_CLOUD_NAME=<Cloudinary cloud name>
CLOUDINARY_API_KEY=<Cloudinary API key>
CLOUDINARY_API_SECRET=<Cloudinary API secret>
FRONTEND_URL=https://golocalmart.vercel.app
BACKEND_BASE_URL=https://local-mart-11yd.onrender.com
CORS_ALLOWED_ORIGINS=https://golocalmart.vercel.app
CSRF_TRUSTED_ORIGINS=https://golocalmart.vercel.app
DEBUG=False
DJANGO_DEBUG=False
```

Stripe is optional for application startup. To enable payments, also set both
`STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`; without them, Stripe checkout
and webhook endpoints return HTTP 503 while the rest of the API remains
available.

After deployment, `https://local-mart-11yd.onrender.com/api/health/` must return
HTTP 200 and report:

```json
{
  "database": { "backend": "postgresql", "persistent": true },
  "media": { "backend": "MediaCloudinaryStorage", "persistent": true }
}
```

Keep Neon's `sslmode=require` and `channel_binding=require` URL parameters in
production. The pooler hostname is preferred for the Render web service.

## Existing data

The old `db.sqlite3` file is ignored and no longer tracked. It remains available
on each developer's machine for local work, but deployment must not use it.
Create the PostgreSQL database and migrate any recoverable SQLite data before
accepting new production writes. Records already lost during an ephemeral
filesystem reset cannot be recovered without an external backup.

Legacy database values such as `profile_photos/example.jpg` refer to local
files, not Cloudinary assets. If the corresponding file is no longer present,
the API returns `null` instead of fabricating a Cloudinary URL that will 404;
the user must upload the original image again. Successful Cloudinary uploads
store public IDs beginning with the configured `media/` prefix.

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
