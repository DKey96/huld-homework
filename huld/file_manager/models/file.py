from django.db import models


class File(models.Model):
    name = models.CharField(max_length=255)
    path = models.FilePathField(max_length=255)
    md5_hash = models.CharField()
    file_number = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["md5_hash"], name="md5_idx"),
        ]
