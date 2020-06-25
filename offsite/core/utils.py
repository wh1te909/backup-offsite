from channels.auth import AuthMiddlewareStack
from knox.auth import TokenAuthentication
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user(access_token):

    try:
        auth = TokenAuthentication()
        token = access_token.decode().split("access_token=")[1]
        user = auth.authenticate_credentials(token.encode())
    except Exception:
        return AnonymousUser()
    else:
        return user[0]


class KnoxAuthMiddlewareInstance:
    """
    https://github.com/django/channels/issues/1399
    """

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):

        q = self.scope["query_string"]

        self.scope["user"] = await get_user(q)

        inner = self.inner(self.scope)
        return await inner(receive, send)


class KnoxAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return KnoxAuthMiddlewareInstance(scope, self)


KnoxAuthMiddlewareStack = lambda inner: KnoxAuthMiddleware(AuthMiddlewareStack(inner))
