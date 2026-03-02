from django.http import HttpRequest
from ninja import Router

from cidb.src.core.models.user import ACAUser
from cidb.src.incidents.api.endpoints.feedback import router as feedback_router


class EditorAuth:
    def __call__(self, request: HttpRequest) -> ACAUser | None:
        if not request.user.is_authenticated:
            return None
        user = request.user
        if user.is_editor or user.is_staff:
            return user
        return None


router = Router(auth=EditorAuth())
router.add_router("/feedback", feedback_router, tags=["feedback"])
