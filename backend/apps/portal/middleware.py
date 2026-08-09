from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def user_for(token):
    try:
        return get_user_model().objects.get(
            pk=AccessToken(token)["user_id"], is_active=True
        )
    except Exception:
        return None


class JwtQueryAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        token = parse_qs(scope.get("query_string", b"").decode()).get("token", [""])[0]
        scope["user"] = await user_for(token)
        return await self.app(scope, receive, send)
