import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Transcription
from .serializers import TranscriptionSerializer
from generators.generator import transcribe_audio_file 

class TranscribeAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        audio_file = request.FILES.get('audio')
        
        if not audio_file:
            return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Save the uploaded file temporarily
        temp_audio_path = f"temp_{audio_file.name}"
        with open(temp_audio_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)

        # Process the audio file
        result = transcribe_audio_file(temp_audio_path)

        # Clean up temporary file
        os.remove(temp_audio_path)

        if "error" in result:
            return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

        # Save transcription to DB
        transcription = Transcription.objects.create(
            user=request.user,
            audio_file=audio_file,
            transcribed_text=result["text"]
        )

        serializer = TranscriptionSerializer(transcription, context={"total_time": result["total_time"]})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TranscriptionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transcriptions = Transcription.objects.filter(user=request.user).order_by('-created_at')
        serializer = TranscriptionSerializer(transcriptions, many=True)
        return Response(serializer.data)