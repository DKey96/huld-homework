from rest_framework.serializers import FileField, Serializer


class UploadSerializer(Serializer):
    file = FileField()

    class Meta:
        fields = ["file"]
