from django.urls import path
from .views import TranscribeAudioView, TranscriptionHistoryView

urlpatterns = [
    path('transcribe/', TranscribeAudioView.as_view(), name='transcribe_audio'),
    path('history/', TranscriptionHistoryView.as_view(), name='transcription_history'),
]