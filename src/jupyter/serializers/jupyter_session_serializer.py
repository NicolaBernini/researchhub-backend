from rest_framework.serializers import ModelSerializer, SerializerMethodField

from jupyter.models import JupyterSession


class JupyterSessionSerializer(ModelSerializer):
    src = SerializerMethodField()

    class Meta:
        model = JupyterSession
        fields = '__all__'
