import note.routing
import notification.routing
import jupyter.routing

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from notification.token_auth import TokenAuthMiddlewareStack

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddlewareStack(
            URLRouter([
                *note.routing.websocket_urlpatterns,
                *notification.routing.websocket_urlpatterns,
                *jupyter.routing.websocket_urlpatterns,
            ])
        )
    ),
})
