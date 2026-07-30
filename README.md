# Local Mart API

Django REST API for products, carts, inventory-safe checkout, Stripe payments, orders, reviews, offers, and seller analytics.

## Local setup

1. Create and activate a virtual environment. On Windows, run `venv\Scripts\activate`.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set local values.
4. Run `python manage.py migrate`.
5. Run `python manage.py runserver`.

On Windows, you can run the project without activating the environment:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Do not use `py manage.py runserver` unless the required packages are installed in your global Python environment; that command bypasses this project's virtual environment.

SQLite is suitable for local development. Set `DATABASE_URL` to PostgreSQL in production. Configure the Stripe webhook endpoint as `/api/payment/stripe/webhook/`; browser redirects never mark an order paid.

Production uploads use Cloudinary. Media records created before Cloudinary was enabled are served from the repository's `media/` directory when `SERVE_LOCAL_MEDIA=True`; this compatibility mode defaults to enabled on Render.

## Verification

```text
python manage.py check --deploy
python manage.py test
python manage.py makemigrations --check --dry-run
```
