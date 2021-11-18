from hashlib import sha1
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from jupyter.models import JupyterSession
from jupyter.serializers import JupyterSessionSerializer
from note.models import Note
from user.models import (
    Gatekeeper
)


class JupyterSessionViewSet(viewsets.ModelViewSet):
    queryset = JupyterSession.objects.all()
    serializer_class = JupyterSessionSerializer
    permission_classes = [AllowAny]

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def get_jupyterhub_user(self, request, pk=None):
        data = request.data
        note_id = data.get('note_id')

        tokens = Token.objects.filter(key=pk)
        if not tokens.exists():
            return Response(status=404)

        token = tokens.first()
        user = token.user
        user_email = user.email

        # Temporary gatekeeping for JupyterHub
        gatekeeper = Gatekeeper.objects.filter(
            email=user_email,
            type='JUPYTER'
        )
        if not gatekeeper.exists():
            return Response(status=404)

        if note_id:
            note = Note.objects.get(id=note_id)
            unified_document = note.unified_document
            user_info = f'NOTE-{note.id}-UNIFIED_DOC-{unified_document.id}'
        else:
            user_info = f'{user.id}-{user_email}'.encode('utf-8')

        hashed_info = sha1(user_info)
        return Response(hashed_info.hexdigest(), status=200)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def sync_jupyter_session(self, request, pk=None):
        data = request.data
        login_token = data.get('login_token')
        session_id = data.get('session_id')
        xsrf_token = data.get('xsrf_token')
        content_type_name = data.get('content_type')
        object_id = data.get('object_id')
        content_type = ContentType.objects.get(model=content_type_name)

        session = self.queryset.filter(
            content_type=content_type,
            object_id=object_id
        )
        if session.exists():
            session = session.first()
        else:
            session = JupyterSession.objects.create(
                content_type=content_type,
                login_token=login_token,
                object_id=object_id,
                session_id=session_id,
                xsrf_token=xsrf_token
            )
        return Response(status=200)
