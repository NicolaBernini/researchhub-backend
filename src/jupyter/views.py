import requests
import base64

from cryptography.fernet import Fernet
from hashlib import sha1
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from jupyter.models import JupyterSession
from jupyter.serializers import JupyterSessionSerializer
from note.models import Note
from researchhub.settings import APP_ENV, JUPYTER_ADMIN_TOKEN
from user.models import (
    Gatekeeper
)
from utils.sentry import log_info


BASE_JUPYTER_URL = 'https://staging-jupyter.researchhub.com'
if 'production' in APP_ENV:
    BASE_JUPYTER_URL = 'https://jupyter.researchhub.com' 


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
            user_info = f'NOTE-{note.id}-UNIFIED_DOC-{unified_document.id}'.encode('utf-8')
            fernet = Fernet(
                base64.b64encode(JUPYTER_ADMIN_TOKEN.encode('utf-8'))
            )
            token = fernet.encrypt(user_info)
        else:
            user_info = f'{user.id}-{user_email}'.encode('utf-8')
            hashed_info = sha1(user_info)
            token = hashed_info.hexdigest()
        data = {
            'user_id': user.id,
            'token': token
        }
        return Response(data, status=200)

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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def get_jupyterhub_file(self, request, pk=None):
        # TODO: update permissions
        data = request.data
        file_name = data.get('file_name')
        note = Note.objects.get(id=pk)
        unified_document = note.unified_document
        user_info = f'NOTE-{note.id}-UNIFIED_DOC-{unified_document.id}'.encode('utf-8')

        hashed_info = sha1(user_info)
        token = hashed_info.hexdigest()
        url = f'{BASE_JUPYTER_URL}/hub/user/{token}/api/contents/{file_name}'
        headers = {'Authorization': f'Token {JUPYTER_ADMIN_TOKEN}'}
        response = requests.get(
            url,
            headers=headers,
            # allow_redirects=False
        )
        status_code = response.status_code
        try:
            data = response.json()
            content = data['content']['cells']
            for cell in content:
                if 'source' in cell:
                    cell['source'] = cell['source'].splitlines(keepends=True)
                if 'outputs' in cell:
                    for output in cell['outputs']:
                        if output['output_type'] == 'stream':
                            output['text'] = output['text'].splitlines(keepends=True)
        except Exception:
            data = response.content

        return Response({'data': data, 'status_code': status_code}, status=200)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def jupyter_file_save_webhook(self, request, pk=None):
        print('------@@@@@@@@@_---------')
        data = request.data
        del data['content']
        print(data)
        try:
            note = Note.objects.get(id=pk)
            data = request.data
            cells = data.get('cells')

            note.notify_jupyter_file_update(cells)
        except Exception:
            pass
        return Response(status=200)
