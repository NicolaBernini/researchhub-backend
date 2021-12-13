from django.urls import re_path

from jupyter import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/jupyter/(?P<uid>\w+)/$',
        consumers.JupyterConsumer.as_asgi()
     )
]
