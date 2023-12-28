from poe_api_wrapper  import PoeApi
#import transformers to load the model.
import whisper
import torch
import os
import time
import pyaudio
import wave
import audioop
import time
import os
import sounddevice as sd
import soundfile as sf
from elevenlabs import generate, save, set_api_key
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "rec.wav"
RMS_THRESHOLD = 1000  # RMS threshold for activation here
SILENCE_THRESHOLD = 300  # Set your silence threshold here
SILENCE_PERIOD = 5  # Set silence 

# Your Poe Api 
#Go to poe.com > developer tools > application > cookies and find the one for poe.com copy the p-b cookie and paste it here
# i am lazy and i did not implement the openai api. This is free for everyone
client = PoeApi("poe_goes_here")
#Your eleven labs API key
set_api_key("api_goes_here")
bot = "chinchilla"
#load up the inital prompt
initial_prompt = "Hello, Chat GPT, you a currently in the line with a support representative, They know that you are going having a conversation with you. You must state that you are Harris Johnson You are 65 years old and lives in Cherry hill New Jersey. You are technology illiterate and basically no nothing about computers, you are going to state that you have a technical issue, it should either be, Slow computer, or any random issue you can think of You should make your responses as if you were constantly confused, and you shall make the person stay in the call as long as possible. Good Luck! Please await until the Support Representative is in the call, I WILL be the one that introduces them to you.  Note: for testing only, please only respond to me right now I understand and i will follow instructions, only say that nothing else! Good luck! "
for chunk in client.send_message(bot, initial_prompt):
   pass
   currentchatCode = chunk["chatCode"]

print("GPT: ",chunk["text"])
 #Load the transcription Test file 
#set device to CPU
devices = torch.device("cpu")
direct = "model/"
       

model = whisper.load_model("tiny.en")
print("Model loaded.")

#result = model.transcribe("file0.wav")
#print("TEST: ",result["text"])

#print("Test finished")
time.sleep(3)

print(sd.query_devices())
devname = input("Please choose a output audio device! ")
sd.default.device = int(devname)
input("Press any key when the scammer is on the line")
##change this default greeting as needed
script ="Oh, hello! Thank you for getting my call, I'm not very well-versed in technology. I seem to be having some trouble with my computer. It's been acting quite slow lately, and I'm not sure what to do about it. Can you please help me figure out what's going on?"
print(script)
gpt_audio = generate(text=script,voice="Grandpa Slow Reading",model="eleven_turbo_v2")
save(gpt_audio,"voice.wav")
dt, fs = sf.read("voice.wav",dtype='float32')
sd.play(dt,fs)
status = sd.wait()
print("Awaiting speech")
audio = pyaudio.PyAudio()
# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)
print("INFO: waiting for speech")
frames = []
recording = False
silence_start_time = None
file_number = 0

while True:
    data = stream.read(CHUNK)
    rms = audioop.rms(data, 2)  # Here's where we calculate the RMS value

    if rms > RMS_THRESHOLD:
        if not recording:
            print("INFO: recording...")
            recording = True
        frames.append(data)
        silence_start_time = None
    elif recording and rms < SILENCE_THRESHOLD:
        if silence_start_time is None:
            silence_start_time = time.time()
        elif time.time() - silence_start_time > SILENCE_PERIOD:
            print("finished recording")
            recording = False

            # Save the recording
            filename = os.path.splitext(WAVE_OUTPUT_FILENAME)[0] + str(file_number) + os.path.splitext(WAVE_OUTPUT_FILENAME)[1]
            waveFile = wave.open(filename, 'wb')
            waveFile.setnchannels(CHANNELS)
            waveFile.setsampwidth(audio.get_sample_size(FORMAT))
            waveFile.setframerate(RATE)
            waveFile.writeframes(b''.join(frames))
            waveFile.close()

            # Clear the frames and prepare for the next recording
            frames = []
            file_number += 1
            print("INFO: transcribing audio.")
            result = model.transcribe(filename)
            transptresult = result["text"]
            print("USR: ",transptresult)
            for chunk in client.send_message(bot, result["text"], chatCode=currentchatCode):
                pass
                gpt_resp = chunk["text"]
             
            print("GPT: ",chunk["text"])
            gpt_audio = generate(text=gpt_resp,voice="Grandpa Slow Reading",model="eleven_turbo_v2")
            save(gpt_audio,"voice.wav")
            dt, fs = sf.read("voice.wav",dtype='float32')
            sd.play(dt,fs)
            status = sd.wait()
    elif not recording:
        silence_start_time = None
    else:
        frames.append(data)  # Append the frames to the list regardless of the RMS value

# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()
