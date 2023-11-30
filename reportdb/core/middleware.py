from django.utils import timezone


class LastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.last_seen = timezone.now()
            request.user.save(update_fields=["last_seen"])

        return self.get_response(request)
