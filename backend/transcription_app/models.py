from django.db import models
from accounts.models import User

class Transcription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transcriptions')
    audio_file = models.FileField(upload_to='audio_uploads/')
    transcribed_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcription {self.id} by {self.user.username}"