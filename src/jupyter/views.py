import base64
import json
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
    Gatekeeper,
    Organization
)
from utils.sentry import log_info


BASE_JUPYTER_URL = 'https://staging-jupyter.researchhub.com'
if 'production' in APP_ENV:
    BASE_JUPYTER_URL = 'https://jupyter.researchhub.com' 


class JupyterSessionViewSet(viewsets.ModelViewSet):
    queryset = JupyterSession.objects.all()
    serializer_class = JupyterSessionSerializer
    permission_classes = [AllowAny]
    # TODO: Update permission class
    lookup_field = 'token'
    jupyter_headers = {'Authorization': f'Token {JUPYTER_ADMIN_TOKEN}'}

    def _get_user_token(self, uid):
        # fernet = Fernet(
        #     base64.b64encode(JUPYTER_ADMIN_TOKEN.encode('utf-8'))
        # )

        # uid = f'ORGANIZATION-{org_id}'.encode('utf8')
        # token = fernet.encrypt(uid)
        if type(uid) is not bytes:
            uid = uid.encode('utf-8')
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

    def _get_researchhub_session(self, request, token):
        data = request.data
        org_id = data.get('org_id')

        user_session = Token.objects.get(key=token)
        organization = Organization.objects.get(id=org_id)
        user = user_session.user

        if not organization.org_has_user(user):
            raise Exception('User does not have permission')
        
        return user, organization

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
            # Server is spinning up
            return True
        elif status_code == 400:
            # Server is already running
            return False
        return response

    def _get_jupyter_server_spawn_progress(self, token):
        url = f'{BASE_JUPYTER_URL}/hub/api/users/{token}/server/progress'
        response = requests.get(
            url,
            headers=self.jupyter_headers,
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            line = line.decode('utf8', 'replace')
            if line.startswith('data:'):
                data = json.loads(line.split(':', 1)[1])
                yield data

    def create(self, request, *args, **kwargs):
        data = request.data
        filename = data.get('filename')
        org_id = data.get('org_id')
        uid = f'ORGANIZATION-{org_id}'
        session, _ = JupyterSession.objects.get_or_create(
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
    def get_jupyterhub_user(self, request, token=None):
        """
        https://staging-jupyter.researchhub.com/login?researchhub-login=gAAAAABh3MhVwgHqJ-dDZpOszgC_q-34qyzMdNz1gx2dtAsb3d9TvjOs2-SVNUmsZoQNZS0whovQPRZmO8V7bG4Ozv9nE9u9DA==
        https://staging-jupyter.researchhub.com/login?researchhub-login=cdff702c6ce2f8ad3f64eaab265fdf9c2a148020&org-id=1
        """
        # session = self.queryset.get(token=token)
        
        user, organization = self._get_researchhub_session(request, token)

        # Temporary gatekeeping for JupyterHub
        # gatekeeper = Gatekeeper.objects.filter(
        #     email=user_email,
        #     type='JUPYTER'
        # )
        # if not gatekeeper.exists():
        #     return Response(status=404)

        uid = f'ORGANIZATION-{organization.id}'
        token = self._get_user_token(uid)
        session, created = JupyterSession.objects.get_or_create(
            token=token,
            uid=uid,
        )

        # org_id = session.uid.split('ORGANIZATION-')[1]
        # org = Organization.objects.get(id=org_id)
        data = {
            'token': token,
            'org_name': organization.name
            # Jupyterhub usernames have a max length of 63
            # 'token': 'asdf'
        }
        return Response(data, status=200)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def get_jupyterhub_file(self, request, token=None):
        # TODO: update permissions
        # Test endpoint
        data = request.data
        filename = data.get('filename')
        session = self.get_object()

        # token = self._get_user_token(org_id)
        token = session.uid
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
    def create_jupyterhub_file(self, request, token=None):
        # TODO: update permissions
        # Test endpoint
        session = self.get_object()

        # token = self._get_user_token(session.uid)
        token = session.uid
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
    def start_jupyter_user_server(self, request, token=None):
        # TODO: update permissions
        user, organization = self._get_researchhub_session(request, token)
        org_uid = f'ORGANIZATION-{organization.id}'
        token = self._get_user_token(org_uid)
        session, created = JupyterSession.objects.get_or_create(
            token=token,
            uid=org_uid,
        )

        data = {}
        try:
            user_exists = self._check_jupyter_user_exists(token)

            if not user_exists:
                self._create_jupyter_user(token)

            server_starting = self._start_jupyter_user_server(token)
            if server_starting:
                for event in self._get_jupyter_server_spawn_progress(
                    token
                ):
                    print(event)
                    session.notify_jupyter_server_progress(event)
                    if event.get('ready'):
                        break

                return Response(
                    {'data': 'Server is running', 'user': created},
                    status=200
                )
        except Exception as e:
            data = {'data': str(e)}
        return Response({'data': data}, status=200)            

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def create_or_get_jupyterhub_session(self, request, token=None):
        # TODO: update permissions
        data = request.data
        user, organization = self._get_researchhub_session(request, token)
        org_uid = f'ORGANIZATION-{organization.id}'
        token = self._get_user_token(org_uid)
        filename = data.get('filename', 'Untitled')
        created = data.get('created', False)

        # token = self._get_user_token(org_id)
        try:
            if created:
                url = f'{BASE_JUPYTER_URL}/user/{token}/api/contents/'
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
                    headers=self.jupyter_headers
                )

            data = response.json()
            content = data['content']['cells']
            for cell in content:
                if 'source' in cell:
                    cell['source'] = cell['source'].splitlines(keepends=True)
                if 'outputs' in cell:
                    for output in cell['outputs']:
                        if output['output_type'] == 'stream':
                            output['text'] = output['text'].splitlines(keepends=True)

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
    def jupyter_file_save_webhook(self, request, token=None):
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
            
            # uid = self._get_user_info_from_token(uid)
            session = self.get_object()
            content = data.get('content')
            cells = content['cells']
            for cell in cells:
                if 'source' in cell:
                    cell['source'] = cell['source'].splitlines(keepends=True)
                if 'outputs' in cell:
                    for output in cell['outputs']:
                        if output['output_type'] == 'stream':
                            output['text'] = output['text'].splitlines(keepends=True)

            session.notify_jupyter_file_update(content)
        except Exception as e:
            print(e)
            pass
        return Response(status=200)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[AllowAny]
    )
    def test(self, request):
        data = request.data
        print(data)
        return Response(status=200)
