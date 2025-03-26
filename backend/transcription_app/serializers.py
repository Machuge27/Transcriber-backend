from rest_framework import serializers
from .models import Transcription

class TranscriptionSerializer(serializers.ModelSerializer):
    total_time = serializers.SerializerMethodField()

    class Meta:
        model = Transcription
        fields = ['id', 'audio_file', 'transcribed_text', 'created_at', 'total_time']

    def get_total_time(self, obj):
        return self.context.get('total_time', None)