import os
import sounddevice as sd
import numpy as np
import threading
import queue
import time
from scipy.io.wavfile import write
from pydub import AudioSegment
import webrtcvad
import openai

class PlantBot:
    def __init__(
        self,
        sample_rate=16000,
        frame_duration_ms=30,  # Frame size in ms for VAD
        vad_aggressiveness=3,  # VAD aggressiveness
        min_speech_duration=1.0,  # Minimum speech duration to process
        silence_duration=1.25,  # Silence duration to consider speech ended
        log_file="conversation_log.txt",
    ):
        self.SAMPLE_RATE = sample_rate
        self.FRAME_DURATION_MS = frame_duration_ms
        self.FRAME_SIZE = int(self.SAMPLE_RATE * self.FRAME_DURATION_MS / 1000)
        self.VAD_AGGRESSIVENESS = vad_aggressiveness
        self.MIN_SPEECH_DURATION = min_speech_duration
        self.SILENCE_DURATION = silence_duration
        self.LOG_FILE = log_file

        # Initialize VAD
        self.vad = webrtcvad.Vad(self.VAD_AGGRESSIVENESS)

        # Initialize variables for speech detection
        self.speech_frames = []
        self.speech_start_time = None
        self.last_speech_time = None
        self.is_speaking = False


        # Load OpenAI API key from environment variable
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def process_audio_frame(self, indata):
        audio_frame = indata[:, 0]  # Mono audio
        pcm_data = (audio_frame * 32768).astype(np.int16).tobytes()
        is_speech = self.vad.is_speech(pcm_data, self.SAMPLE_RATE)
        return is_speech

    def on_speech_start(self):
        print("Speech started!")

    def on_speech_end(self):
        print("Speech ended.")
        # Check if speech duration was longer than minimum duration
        speech_duration = self.last_speech_time - self.speech_start_time
        if speech_duration >= self.MIN_SPEECH_DURATION:
            print("Processing audio...")
            self.save_audio_file()
            
        else:
            print("Speech too short, discarding.")
        # Clear speech frames for the next utterance
        self.speech_frames = []

    def save_audio_file(self):
        
        if self.speech_frames:
            audio_np = np.concatenate(self.speech_frames, axis=0)
            wav_file = "output.wav"
            write(wav_file, self.SAMPLE_RATE, audio_np)

            # Convert WAV to MP3
            #sound = AudioSegment.from_wav(wav_file)
            #mp3_file = "output.mp3"
            #sound.export(mp3_file, format="mp3")
            #os.remove(wav_file)
            #self.process_audio_with_openai(mp3_file)
            starttime = time.time()
            self.process_audio_with_openai(wav_file)
            endtime = time.time()
            execution_time = endtime - starttime
            print(f"Execution Time: {execution_time:.4f} seconds")
        else:
            print("No audio data to save.\n")

    def process_audio_with_openai(self, wav_file):
        audio_file = open(wav_file, "rb")
        #audio_file = open(mp3_file, "rb")
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        user_input = transcript.text
        #print("Transcript:", user_input, "\n")
    
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant."
                        "You impersonate a plant. "
                        "This GPT is a model that provides auto-therapy for whoever chats with it. "
                        "Try to relate moods to ecology, provide insights as through the lens of a plant."
                        "Be compassionate. "
                        "Keep answers short: about 1 or 2 short paragraphs of 2 or 3 sentences of about 10 words."
                        "This model needs to also reads the weather and mimick a persona that matches those of someone having the SAD condition (seasonal affective disorder)."
                    ),
                },
                {"role": "user", "content": user_input}
            ],
        )
        gpt4_response = response.choices[0].message.content
        print("Cyberplant:", gpt4_response)

        user_choice = input("Press Enter to continue or type 'q' to quit: ").strip().lower()
        if user_choice == 'q':
            print("Exiting the program.")
            exit()
        # Log the conversation
        #self.log_conversation(user_input, gpt4_response)

    def log_conversation(self, user_input, gpt4_response):
        with open(self.LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write("User:\n")
            log_file.write(user_input + "\n")
            log_file.write("Cyberplant:\n")
            log_file.write(gpt4_response + "\n")
            log_file.write("\n" + "=" * 40 + "\n\n")

    def start(self):
        print("Listening for speech. Press Ctrl+C to exit.")
        try:
            with sd.InputStream(
                channels=1,
                samplerate=self.SAMPLE_RATE,
                blocksize=self.FRAME_SIZE,
                callback=self.callback,
            ):
                while True:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")

    def callback(self, indata, frames, time_info, status):
        current_time = time.time()
        is_speech = self.process_audio_frame(indata)

        if is_speech:
            if not self.is_speaking:
                self.speech_start_time = current_time
                self.on_speech_start()
            self.is_speaking = True
            self.last_speech_time = current_time
            # Collect speech frames
            self.speech_frames.append(indata.copy())
        else:
            if self.is_speaking:
                # Check if silence duration has passed
                if current_time - self.last_speech_time >= self.SILENCE_DURATION:
                    self.is_speaking = False
                    self.on_speech_end()
            # Else, do nothing, continue listening

if __name__ == "__main__":
    plantbot = PlantBot()
    plantbot.start()
