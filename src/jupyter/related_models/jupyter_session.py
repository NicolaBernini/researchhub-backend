from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from utils.models import DefaultModel


class JupyterSession(DefaultModel):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    login_token = models.CharField(
        max_length=256
    )
    object_id = models.PositiveIntegerField()
    session_id = models.CharField(
        max_length=64
    )
    source = GenericForeignKey(
        'content_type',
        'object_id'
    )
    xsrf_token = models.CharField(
        max_length=64
    )
