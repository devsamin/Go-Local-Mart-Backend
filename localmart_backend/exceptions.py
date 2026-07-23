from cloudinary.exceptions import Error as CloudinaryError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Return predictable error payloads while preserving DRF status codes."""
    response = exception_handler(exc, context)
    if response is None:
        if isinstance(exc, CloudinaryError):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "media_service_unavailable",
                        "message": "The image service is temporarily unavailable. Please try again without an image or retry shortly.",
                    },
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return None

    detail = response.data
    if isinstance(detail, dict) and set(detail) == {"detail"}:
        message = str(detail["detail"])
        fields = None
    else:
        message = "Please correct the highlighted fields."
        fields = detail

    response.data = {
        "success": False,
        "error": {"code": getattr(exc, "default_code", "request_error"), "message": message},
    }
    if fields is not None:
        response.data["error"]["fields"] = fields
    return response
