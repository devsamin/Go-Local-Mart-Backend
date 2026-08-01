from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Report dependency health and persistence configuration without secrets."""
    try:
        connection.ensure_connection()
        database_ok = connection.is_usable()
    except Exception:
        database_ok = False

    database_backend = connection.vendor
    media_backend = default_storage.__class__.__module__
    persistent_database = database_backend == "postgresql"
    persistent_media = media_backend.startswith("cloudinary_storage.")
    production = settings.IS_PRODUCTION
    persistence_ok = not production or (persistent_database and persistent_media)
    healthy = database_ok and persistence_ok

    response = JsonResponse(
        {
            "status": "ok" if healthy else "degraded",
            "environment": "production" if production else "local",
            "database": {
                "available": database_ok,
                "backend": database_backend,
                "persistent": persistent_database,
            },
            "media": {
                "backend": default_storage.__class__.__name__,
                "persistent": persistent_media,
            },
        },
        status=200 if healthy else 503,
    )
    response["Cache-Control"] = "no-store"
    return response
