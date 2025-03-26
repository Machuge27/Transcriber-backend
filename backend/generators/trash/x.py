import speech_recognition as sr
from pydub import AudioSegment
import os
import io
import time
import tempfile
import concurrent.futures

class AudioTranscriber:
    def __init__(self, segment_duration=120):  # Default 2-minute segments
        self.recognizer = sr.Recognizer()
        self.segment_duration = segment_duration  # Duration in seconds
        self.temp_files = []

    def convert_to_wav(self, audio_file_path):
        """Convert non-WAV audio files to WAV format."""
        if audio_file_path.lower().endswith('.wav'):
            print("Audio is already in WAV format. No conversion needed.")
            return audio_file_path

        print("Converting audio to WAV format...")
        start_time = time.time()
        
        audio = AudioSegment.from_file(audio_file_path)
        wav_file_path = audio_file_path.rsplit('.', 1)[0] + '.wav'
        audio.export(wav_file_path, format='wav')

        conversion_time = time.time() - start_time
        print(f"Conversion completed in {conversion_time:.4f} seconds.")
        
        return wav_file_path

    def split_audio(self, audio_file_path):
        """Split long audio file into segments."""
        print(f"Splitting audio into {self.segment_duration}-second segments...")
        start_time = time.time()
        
        # Convert to wav if needed
        wav_source = self.convert_to_wav(audio_file_path)
        
        # Load the audio
        audio = AudioSegment.from_file(wav_source)
        
        # Calculate segment length in milliseconds
        segment_length = self.segment_duration * 1000
        
        # Split the audio
        segments = []
        for i in range(0, len(audio), segment_length):
            segment = audio[i:i+segment_length]
            
            # Create a temporary file for each segment
            temp_file = tempfile.mktemp(suffix=f'_segment_{i//segment_length}.wav')
            self.temp_files.append(temp_file)
            segment.export(temp_file, format='wav')
            segments.append(temp_file)
        
        split_time = time.time() - start_time
        print(f"Audio split into {len(segments)} segments in {split_time:.4f} seconds.")
        return segments

    def transcribe_segment(self, audio_file_path):
        """Transcribe a single audio segment."""
        print(f"Transcribing segment: {os.path.basename(audio_file_path)}")
        
        try:
            with sr.AudioFile(audio_file_path) as source:
                print(f"  Adjusting for ambient noise in {os.path.basename(audio_file_path)}...")
                noise_start = time.time()
                self.recognizer.adjust_for_ambient_noise(source)  # Reduce noise effects
                noise_time = time.time() - noise_start

                print(f"  Recording audio segment {os.path.basename(audio_file_path)}...")
                record_start = time.time()
                audio = self.recognizer.record(source)
                record_time = time.time() - record_start

                try:
                    print(f"  Initiating transcription for {os.path.basename(audio_file_path)}...")
                    transcribe_start = time.time()
                    transcribed_text = self.recognizer.recognize_google(audio)
                    transcribe_time = time.time() - transcribe_start

                    return {
                        "text": transcribed_text,
                        "noise_reduction_time": round(noise_time, 4),
                        "recording_time": round(record_time, 4),
                        "transcription_time": round(transcribe_time, 4),
                    }

                except sr.UnknownValueError:
                    print(f"  No speech detected in {os.path.basename(audio_file_path)}")
                    return {"text": ""}
                except sr.RequestError as e:
                    print(f"  API request failed for {os.path.basename(audio_file_path)}: {e}")
                    return {"error": f"API request failed: {e}"}

        except Exception as e:
            print(f"  Error processing segment {os.path.basename(audio_file_path)}: {e}")
            return {"error": f"Error processing segment: {e}"}

    def transcribe_audio_file(self, audio_file_path):
        """Transcribe long audio file by splitting into segments and using threading."""
        print("Starting audio transcription...")
        start_time = time.time()
        
        # Split the audio into segments
        segments = self.split_audio(audio_file_path)
        
        # Transcribe segments in parallel
        print("Transcribing segments using multi-threading...")
        transcriptions = []
        segment_details = []
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all segments for transcription
            future_to_segment = {
                executor.submit(self.transcribe_segment, segment): segment 
                for segment in segments
            }
            
            for future in concurrent.futures.as_completed(future_to_segment):
                segment = future_to_segment[future]
                try:
                    result = future.result()
                    if 'text' in result and result['text']:
                        transcriptions.append(result['text'])
                        segment_details.append(result)
                except Exception as exc:
                    print(f"Segment {segment} generated an exception: {exc}")
        
        # Combine transcriptions
        full_transcription = " ".join(transcriptions)
        
        # Cleanup temporary files
        self.cleanup_temp_files()
        
        total_time = time.time() - start_time
        print(f"Transcription completed in {total_time:.4f} seconds.")
        
        return {
            "text": full_transcription,
            "segment_details": segment_details,
            "total_segments": len(segments),
            "total_time": round(total_time, 4)
        }

    def cleanup_temp_files(self):
        """Remove temporary files."""
        print("Cleaning up temporary files...")
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
                print(f"  Removed: {temp_file}")
            except Exception as e:
                print(f"  Error removing temporary file {temp_file}: {e}")
        self.temp_files.clear()
        print("Temporary files cleanup completed.")

def main():
    # Example usage
    audio_file_path = "./trash/sample.mp3"  # Change to your audio file path
    
    # Create transcriber with 2-minute segments
    transcriber = AudioTranscriber(segment_duration=120)
    
    try:
        result = transcriber.transcribe_audio_file(audio_file_path)
        
        print("\n--- Transcription Results ---")
        print("Full Transcription:", result['text'])
        
        print("\n--- Segment Details ---")
        for i, detail in enumerate(result['segment_details'], 1):
            print(f"Segment {i}:")
            for key, value in detail.items():
                print(f"  {key}: {value}")
        
        print("\n--- Summary ---")
        print("Total Time:", result['total_time'], "seconds")
        print("Total Segments:", result['total_segments'])
    
    except Exception as e:
        print(f"Transcription error: {e}")

if __name__ == "__main__":
    main()