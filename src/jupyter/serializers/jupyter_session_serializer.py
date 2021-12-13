from rest_framework.serializers import ModelSerializer, SerializerMethodField

from jupyter.models import JupyterSession


class JupyterSessionSerializer(ModelSerializer):

    class Meta:
        model = JupyterSession
        fields = '__all__'
