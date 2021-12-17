from django.db import models

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from utils.models import DefaultModel


class JupyterSession(DefaultModel):
    filename = models.CharField(max_length=128)
    token = models.CharField(max_length=64)
    uid = models.CharField(max_length=64)

    def notify_jupyter_server_progress(self, data):
        uid = self.uid
        room = f'JUPYTER_{uid}'
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room,
            {
                'type': 'notify_jupyter_server_progress',
                'data': data,
            }
        )

    def notify_jupyter_file_update(self, data):
        uid = self.uid
        room = f'JUPYTER_{uid}'
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room,
            {
                'type': 'notify_jupyter_file_update',
                'data': data,
            }
        )
