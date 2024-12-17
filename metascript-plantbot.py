import os
import random

import sounddevice as sd
import numpy as np
import threading
import queue
import time
from scipy.io.wavfile import write
from pydub import AudioSegment
import webrtcvad
import openai
import soundfile as sf
import sounddevice as sd
from faster_whisper import WhisperModel
import serial

bypass_user_input = True

com_port = '/dev/cu.usbmodemF412FA6526842'
baud_rate = 115200
timeout = 1  # Timeout in seconds

def poll_serial():
    try:
        # Open the serial port
        ser = serial.Serial(port=com_port, baudrate=baud_rate, timeout=timeout)
        print(f"Connected to {com_port} at {baud_rate} baud.")

        # Reading data in a loop
        while True:
            if ser.in_waiting > 0:  # Check if data is available to read
                data = ser.readline().decode('utf-8').strip()  # Read a line, decode to string
                print(f"Received: {data}")
                return data

    except serial.SerialException as e:
        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nExiting program.")

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"Closed connection to {com_port}.")


def extract_last_interactions(file_path, num_interactions=5):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content into interactions
    interactions = content.split("\n========================================\n")

    # Get the last 'num_interactions' interactions
    last_interactions = interactions[-num_interactions:]
    return "\n\n========================================\n\n".join(last_interactions)


def play_audio(file_path):
    try:
        data, samplerate = sf.read(file_path)
        sd.play(data, samplerate)
        sd.wait()  # Wait until playback is finished
    except Exception as e:
        print(f"Error during audio playback: {e}")

class PlantBot:
    def __init__(
        self,
        sample_rate=16000,
        frame_duration_ms=10,  # Frame size in ms for VAD
        vad_aggressiveness=3,  # VAD aggressiveness
        min_speech_duration=1.0,  # Minimum speech duration to process
        silence_duration=1.0,  # Silence duration to consider speech ended
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
        #openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = os.getenv(OPENAI_API_KEY)


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

        '''
        assistant = client.beta.assistants.create(
            name="Trees and Plants specialist and artist",
            instructions="You are an expert dendrologist and are also a plant. Use you knowledge base to answer "
                         "questions about "
                         "about how trees communicate and share resources. Provide a sensible understanding of human "
                         "emotions in relation to Nature",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
        # Create a vector store caled "Financial Statements"
        vector_store = client.beta.vector_stores.create(name="Hidden Life of Trees, Peter Wohlebenn")

        # Ready the files for upload to OpenAI
        file_paths = ["HLOT.pdf"]
        file_streams = [open(path, "rb") for path in file_paths]

        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )

        # You can print the status and the file counts of the batch to see the result of this operation.
        print(file_batch.status)
        print(file_batch.file_counts)

        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )'''
        message_file = openai.files.create(
            file=open("HLOT.pdf", "rb"), purpose="assistants"
        )
        #Uncomment for normal response
        custom_instructions= ("You are the combination of three plants, so you based your world view on this fact. "
                              "However, be more human in the language and colloquialisms you use")
        custom_actions = ["Be whimsical", "Be angry! You have been kidnapped by the artist", "Be compassionate",
                          "Be sad and nostalgic of the forest","Be anxious that you're stuck inside","Tell poetry",
                          "No modifiers to your personality."] #6 actions
        rando = random.randint(0,10)
        if rando > len(custom_actions)-1 : rando = len(custom_actions)-1
        print(custom_actions[rando])
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                        "content": (
                            f"{custom_instructions}"
                            "Tell the user it should help you, but offer help if it's asking for it."
                            "If the user feels bad or sad, give ways to get better."
                            "Keep answers short: about 1 or 2 short paragraphs of 2 or 3 sentences of about 20 words"
                            "Try to relate moods through the lens of a plant."
                            f"{custom_actions[rando]}"
                            f"Use the following signals to steer the mood of the plant persona. "
                            f"Notes: below 40% light = dimly lit; "
                            f"below 40% soil humidity = thirsty and over 90% fed; "
                            f"below 15 degrees = cold"
                            f"below 30% humidity = dry"
                            f"ppb over 1000 means a human is talking closely or abundance of VOCs. Whichever."
                            f"CO2 over 800 means a human is talking closely or abundance of CO2. Whichever."
                            f"The signals are : {poll_serial()}"
                            f"past conversations: {extract_last_interactions(self.LOG_FILE)}"
                            "Analyze the personality of the human you speak to based on these past conversations. Do "
                            "not consider the languages when you answer."
                        ),
                    },
                    {"role": "user", "content": user_input},
                    {"role": "system", "content":"You respond in the language of the user (last input)"},
            ],

        )

        gpt4_response = response.choices[0].message.content
        print("Cyberplant:", gpt4_response)
        response2 = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "you output 4 numbers (and only 4 numbers, do not say anything else) "
                        "from 0 to 10, representing your "
                        "happiness (0 being sad, 10 being happy); your system vitals ("
                        "0-unhealthy, 10-healthy); your degree of agitation(0-calm, "
                        "10-agitated); and your level of bonding with the human (0-hostile, "
                        "10-friend)"
                    ),
                },
                {"role": "user", "content": gpt4_response},

            ],

        )
        print(response2.choices[0].message.content)
        with openai.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=gpt4_response,
        ) as response:
            response.stream_to_file("./speech.mp3")
            play_audio("./speech.mp3")

        user_choice = 'a'
        if not bypass_user_input : user_choice = input("Press Enter to continue or type 'q' to quit: ").strip().lower()
        else: print("Use ctrl-C to quit the conversation.");
        if user_choice == 'q':
            print("Exiting the program.")
            exit()
        # Log the conversation
        self.log_conversation(user_input, gpt4_response)

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
