from django.utils import timezone
from rest_framework import authentication, exceptions

from core.models import ClientAPIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Expects header: Authorization: Api-Key <secret>
    or: X-Api-Key: <secret>
    """

    keyword = "Api-Key"

    def authenticate(self, request):
        key = request.headers.get("X-Api-Key") or request.headers.get("X-API-Key")
        if not key:
            auth = request.headers.get("Authorization", "")
            if auth.startswith(self.keyword + " "):
                key = auth[len(self.keyword) + 1 :].strip()
        if not key:
            return None

        digest = ClientAPIKey.hash_secret(key)
        try:
            api_key = ClientAPIKey.objects.select_related("user").get(
                key_hash=digest,
                is_active=True,
            )
        except ClientAPIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid API key.")

        ClientAPIKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())
        return (api_key.user, api_key)
