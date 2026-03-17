from django.db import models


# Create your models here.


class CorruptionEntry(models.Model):
    title = models.CharField(max_length=256)
    description = models.TextField()

class EntryMedia(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    MEDIA_TYPE_CHOICES = [(IMAGE, 'Image'), (VIDEO, 'Video')]

    entry = models.ForeignKey(CorruptionEntry, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to='corruption_media/')