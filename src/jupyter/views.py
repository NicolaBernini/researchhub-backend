import base64
import re
import requests

from cryptography.fernet import Fernet, InvalidToken
from hashlib import sha1
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
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
    lookup_field = 'uid'
    jupyter_headers = {'Authorization': f'Token {JUPYTER_ADMIN_TOKEN}'}

    def _get_user_token(self, uid):
        # fernet = Fernet(
        #     base64.b64encode(JUPYTER_ADMIN_TOKEN.encode('utf-8'))
        # )

        if type(uid) is not bytes:
            uid = uid.encode('utf-8')
        # token = fernet.encrypt(uid)
        hashed_info = sha1(uid)
        token = hashed_info.hexdigest()
        return token

    def _get_user_info_from_token(self, token):
        try:
            fernet = Fernet(
                base64.b64encode(JUPYTER_ADMIN_TOKEN.encode('utf-8'))
            )
            user_info = fernet.decrypt(token)
        except InvalidToken:
            return ''
        return user_info

    def _check_jupyter_user_exists(self, token):
        url = f'{BASE_JUPYTER_URL}/hub/api/users/{token}'
        response = requests.get(url=url, headers=self.jupyter_headers)
        if response.status_code == 200:
            return True
        return False

    def _create_jupyter_user(self, token):
        url = f'{BASE_JUPYTER_URL}/hub/api/users/{token}'
        response = requests.post(url=url, headers=self.jupyter_headers)
        if response.status_code == 201:
            return response.json()
        return response

    def _start_jupyter_user_server(self, token):
        url = f'{BASE_JUPYTER_URL}/hub/api/users/{token}/server'
        response = requests.post(url=url, headers=self.jupyter_headers)
        status_code = response.status_code
        if response.status_code == 202:
            return True
        elif status_code == 400:
            return False
        return response

    def _get_jupyter_server_spawn_progress(self, token):
        request_session = requests.Session()
        url = f'{BASE_JUPYTER_URL}/hub/api/users/{token}/server/progress'
        with request_session.get(
            url,
            headers=self.jupyter_headers,
            stream=True
        ) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        print(line)
        return

    def create(self, request, *args, **kwargs):
        data = request.data
        filename = data.get('filename')
        uid = get_random_string(length=32)
        session = JupyterSession.objects.create(
            uid=uid,
            filename=filename
        )
        serializer = self.serializer_class(session)

        return Response(serializer.data, status=200)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def get_jupyterhub_user(self, request, uid=None):
        session = self.get_object()

        # Temporary gatekeeping for JupyterHub
        # gatekeeper = Gatekeeper.objects.filter(
        #     email=user_email,
        #     type='JUPYTER'
        # )
        # if not gatekeeper.exists():
        #     return Response(status=404)

        uid = session.uid
        token = self._get_user_token(uid)
        data = {
            'token': token
        }
        return Response(data, status=200)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def get_jupyterhub_file(self, request, uid=None):
        # TODO: update permissions
        data = request.data
        filename = data.get('filename')
        session = self.get_object()

        token = self._get_user_token(session.uid)
        url = f'{BASE_JUPYTER_URL}/hub/user/{token}/api/contents/{filename}'
        response = requests.get(
            url,
            headers=self.jupyter_headers,
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
        permission_classes=[IsAuthenticated]
    )
    def create_jupyterhub_file(self, request, uid=None):
        # TODO: update permissions
        data = request.data
        filename = data.get('filename')
        session = self.get_object()

        token = self._get_user_token(session.uid)
        url = f'{BASE_JUPYTER_URL}/user/{token}/api/contents/'
        response = requests.post(
            url,
            json={'ext': '.ipynb'},
            headers=self.jupyter_headers,
            # allow_redirects=False
        )
        status_code = response.status_code
        data = response.json()

        return Response({'data': data, 'status_code': status_code}, status=200)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def create_or_get_jupyterhub_session(self, request, uid=None):
        # TODO: update permissions
        data = request.data
        filename = data.get('filename', 'Untitled')

        session, created = JupyterSession.objects.get_or_create(
            filename=filename,
            uid=uid
        )
        token = self._get_user_token(uid)

        try:
            user_exists = self._check_jupyter_user_exists(token)

            if not user_exists:
                self._create_jupyter_user(token)

            server_starting = self._start_jupyter_user_server(token)
            if server_starting:
                # return Response({'data': 'Server is starting'}, status=200)
                self._get_jupyter_server_spawn_progress(token)

            base_file_url = f'{BASE_JUPYTER_URL}/user/{token}/api/contents'
            headers = {'Authorization': f'Token {JUPYTER_ADMIN_TOKEN}'}

            if created:
                url = base_file_url
                response = requests.post(
                    url,
                    json={'ext': '.ipynb'},
                    headers=self.jupyter_headers,
                    # allow_redirects=False
                )
            else:
                url = f'{BASE_JUPYTER_URL}/hub/user/{token}/api/contents/{filename}.ipynb'
                response = requests.get(
                    url,
                    headers=headers
                )

            data = response.json()
        except Exception as e:
            data = {'data': str(e)}
        return Response(
            {'data': data, 'status_code': response.status_code},
            status=200
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def jupyter_file_save_webhook(self, request, uid=None):
        # TODO: Permissions - only allow requests within vpc or something
        data = request.data
        try:
            # user_info = self._get_user_info_from_token(pk)
            # note_regex = r'(?<=NOTE-).*(?=-UNIFIED_DOC)'
            # # unified_doc_regex = r'(?<=UNIFIED_DOC-).*(?=)'
            # note_search = re.search(note_regex, user_info)

            # if not note_search:
            #     return Response(status=200)
            # else:
            #     note_id = note_search.group()
            
            session = self.get_object()
            data = request.data
            cells = data.get('cells')

            session.notify_jupyter_file_update(cells)
        except Exception as e:
            print(e)
            pass
        return Response(status=200)
