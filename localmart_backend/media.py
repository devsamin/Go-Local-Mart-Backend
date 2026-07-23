def optimized_image_url(file_field, request=None, width=1200):
    """Return a responsive Cloudinary URL while retaining local-storage support."""
    if not file_field:
        return None
    url = file_field.url
    if "/upload/" in url and "/upload/f_auto," not in url:
        url = url.replace("/upload/", f"/upload/f_auto,q_auto,c_limit,w_{width}/", 1)
    if request and url.startswith("/"):
        return request.build_absolute_uri(url)
    return url
