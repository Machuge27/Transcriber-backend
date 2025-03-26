import speech_recognition as sr
from pydub import AudioSegment
import os
import io
import time

recognizer = sr.Recognizer()

def convert_to_wav(audio_file_path):
    """Convert non-WAV audio files to WAV format."""
    if audio_file_path.lower().endswith('.wav'):
        return audio_file_path  # No conversion needed

    print("Converting audio to WAV format...")
    start_time = time.time()
    
    audio = AudioSegment.from_file(audio_file_path)
    wav_file_path = audio_file_path.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_file_path, format='wav')

    conversion_time = time.time() - start_time
    print(f"Conversion completed in {conversion_time:.4f} seconds.")
    
    return wav_file_path, conversion_time

def transcribe_audio_file(audio_file_path):
    """Transcribe audio and measure time taken for each process."""
    try:
        print("Checking and converting audio format...")
        audio_source, conversion_time = convert_to_wav(audio_file_path)

        with sr.AudioFile(audio_source) as source:
            print("Adjusting for ambient noise...")
            noise_start = time.time()
            recognizer.adjust_for_ambient_noise(source)  # Reduce noise effects
            noise_time = time.time() - noise_start

            print("Recording audio...")
            record_start = time.time()
            audio = recognizer.record(source)
            record_time = time.time() - record_start

        try:
            print("Initiating transcription...")
            transcribe_start = time.time()
            transcribed_text = recognizer.recognize_google(audio)
            transcribe_time = time.time() - transcribe_start

            total_time = conversion_time + noise_time + record_time + transcribe_time

            return {
                "text": transcribed_text,
                "total_time": round(total_time, 4)  # Round for better readability
            }

        except sr.UnknownValueError:
            return {"error": "Could not understand the audio.", "total_time": None}
        except sr.RequestError as e:
            return {"error": f"API request failed: {e}", "total_time": None}

    except Exception as e:
        return {"error": f"Error processing audio: {e}", "total_time": None}

if __name__ == "__main__":
    audio_file_path = "./trash/sample.mp3"  # Example file path
    result = transcribe_audio_file(audio_file_path)
    print("Transcription Result:", result)