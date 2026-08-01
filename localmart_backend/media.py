from pathlib import Path
from urllib.parse import quote

from django.conf import settings


def _is_unmigrated_cloudinary_name(file_field):
    """Return whether a local database path was never uploaded to Cloudinary.

    django-cloudinary-storage prepends its media prefix to successful uploads
    and stores that returned public ID on the model. Calling ``.url`` for an
    older FileSystemStorage value otherwise fabricates a Cloudinary URL for an
    asset that was never uploaded and therefore always returns 404.
    """
    storage = getattr(file_field, "storage", None)
    storage_module = storage.__class__.__module__ if storage else ""
    if not storage_module.startswith("cloudinary_storage."):
        return False

    prefix_getter = getattr(storage, "_get_prefix", None)
    prefix = str(prefix_getter() if prefix_getter else settings.MEDIA_URL).strip("/")
    name = str(getattr(file_field, "name", "") or "").replace("\\", "/").lstrip("/")
    return bool(prefix and name and not (name == prefix or name.startswith(f"{prefix}/")))


def _local_media_url(file_field, request=None):
    """Return a URL for a legacy file that is bundled in MEDIA_ROOT."""
    if not (settings.DEBUG or settings.SERVE_LOCAL_MEDIA):
        return None

    name = str(getattr(file_field, "name", "") or "").replace("\\", "/").lstrip("/")
    if not name:
        return None

    media_root = Path(settings.MEDIA_ROOT).resolve()
    candidate = (media_root / name).resolve()
    try:
        candidate.relative_to(media_root)
    except ValueError:
        return None

    if not candidate.is_file():
        return None

    url = f"{settings.MEDIA_URL.rstrip('/')}/{quote(name, safe='/')}"
    return request.build_absolute_uri(url) if request else url


def optimized_image_url(file_field, request=None, width=1200):
    """Return a responsive Cloudinary URL while retaining local-storage support."""
    if not file_field:
        return None

    # Records created before Cloudinary was enabled still contain local paths
    # such as products/example.jpg. The corresponding Cloudinary URLs are 404s,
    # so prefer the bundled legacy file when it exists.
    local_url = _local_media_url(file_field, request=request)
    if local_url:
        return local_url

    # Let the client show its avatar fallback until the user re-uploads the
    # missing legacy image. The new upload will store a real Cloudinary ID.
    if _is_unmigrated_cloudinary_name(file_field):
        return None

    url = file_field.url
    if "/upload/" in url and "/upload/f_auto," not in url:
        url = url.replace("/upload/", f"/upload/f_auto,q_auto,c_limit,w_{width}/", 1)
    if request and url.startswith("/"):
        return request.build_absolute_uri(url)
    return url
