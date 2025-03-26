import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile
import time
import concurrent.futures

class AudioTranscriber:
    def __init__(self, segment_duration=120):  # Default 2-minute segments
        self.recognizer = sr.Recognizer()
        self.segment_duration = segment_duration
        self.temp_files = []

    def convert_to_wav(self, audio_file_path):
        """Convert non-WAV audio files to WAV format."""
        if audio_file_path.lower().endswith('.wav'):
            return audio_file_path

        audio = AudioSegment.from_file(audio_file_path)
        wav_file_path = audio_file_path.rsplit('.', 1)[0] + '.wav'
        audio.export(wav_file_path, format='wav')
        return wav_file_path

    def split_audio(self, audio_file_path):
        """Split long audio file into segments."""
        wav_source = self.convert_to_wav(audio_file_path)
        audio = AudioSegment.from_file(wav_source)
        
        segment_length = self.segment_duration * 1000
        
        segments = []
        for i in range(0, len(audio), segment_length):
            segment = audio[i:i+segment_length]
            
            temp_file = tempfile.mktemp(suffix=f'_segment_{i//segment_length}.wav')
            self.temp_files.append(temp_file)
            segment.export(temp_file, format='wav')
            segments.append(temp_file)
        
        return segments

    def transcribe_segment(self, audio_file_path):
        """Transcribe a single audio segment."""
        try:
            with sr.AudioFile(audio_file_path) as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.record(source)

                try:
                    transcribed_text = self.recognizer.recognize_google(audio)
                    return transcribed_text
                except sr.UnknownValueError:
                    return ""
                except sr.RequestError:
                    return ""

        except Exception:
            return ""

    def transcribe_audio_file(self, audio_file_path):
        """Transcribe long audio file by splitting into segments and using threading."""
        start_time = time.time()
        
        # Split the audio into segments
        segments = self.split_audio(audio_file_path)
        
        # Transcribe segments in parallel
        transcriptions = []
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            transcriptions = list(executor.map(self.transcribe_segment, segments))
        
        # Combine transcriptions
        full_transcription = " ".join(filter(bool, transcriptions))
        
        # Cleanup temporary files
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass
        
        total_time = time.time() - start_time
        
        return {
            "text": full_transcription,
            "total_time": round(total_time, 4)
        }

def transcribe_audio_file(audio_file_path):
    """Wrapper function for easy use."""
    transcriber = AudioTranscriber()
    return transcriber.transcribe_audio_file(audio_file_path)

if __name__ == "__main__":
    audio_file_path = "./trash/sample.mp3"  # Change to your audio file path
    result = transcribe_audio_file(audio_file_path)
    print("Transcription:", result['text'])
    print("Total Time:", result['total_time'], "seconds")