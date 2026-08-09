from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from apps.accounts.models import User
@database_sync_to_async
def user_for(token):
    try:return User.objects.get(pk=AccessToken(token)["user_id"])
    except Exception:return None
class JwtQueryAuthMiddleware:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        token=parse_qs(scope.get("query_string",b"").decode()).get("token",[""])[0];scope["user"]=await user_for(token);return await self.app(scope,receive,send)
