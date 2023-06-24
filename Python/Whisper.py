################# Imports #################
import subprocess
import re
import whisper
import torch
#import torch_directml
import json
import openai

from pathlib import Path
from pyannote.audio import Pipeline
from pydub import AudioSegment
from datetime import timedelta

################# Global Vars #################
meeting = "/Videos_and_Audio/Test2.mp4" #Path to the video
model = "" #Whisper Model
number_of_speakers = 0

output_path = "/videos/"
access_token = ""
openai_key = ""
################# Methods #################
""" Extracts the audio of a video

The implementation with the ffmpeg wrapper is missing
"""
def get_wav(video: str):
    print("command")
    command = f"ffmpeg -i {video} -ab 160k -ac 2 -ar 44100 -vn {video}.wav"
    print("subcommand")
    subprocess.call(command, shell=True)
    return ""
    
""" Distinguishes the different speakers in the meeting

This methodes uses https://github.com/pyannote/pyannote-audio to find the times
different speakers speak. It returns a list of timestamps at which everyone is 
speaking, which can later be combined with the output of the transcription

Works only on CPU with an AMD GPU => it therefor is slow. Pytorch with DirectMl
throws errors.

The code is copyed more or less directly from: https://github.com/Majdoddin/nlp

Args:
    audio: a .wav file containing

Returns:
    a .txt file which contains the time stamps of the different speakers.
"""
def get_speakers(audio: str):
    if not(access_token):
        from huggingface_hub import notebook_login
        print("login")
        notebook_login()

    print("pipeline")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                        use_auth_token=access_token)
    print("dz")
    dz = pipeline(audio)  

    with open("diarization.txt", "w") as text_file:
        text_file.write(str(dz))
    
    print(*list(dz.itertracks(yield_label = True))[:10], sep="\n")

""" Groups the text spoken by the same speaker

The Models output is suboptimal in the way that it not only displays the
times the speaker changes, but also splitts parts of the same speech seemingly 
randomly (while still accuratly predicting who is the speaker). Theese random 
cuts are rectified with this method.  

The code is copyed more or less directly from: https://github.com/Majdoddin/nlp

Args:
    diarization_file: the file with the output of getspeakers()

Return:
    groups: the grouped speaker information
"""
def grouping_diarization(diarization_file: str, audio_file: str):
    dzs = open(diarization_file).read().splitlines()

    groups = []
    g = []
    lastend = 0

    for d in dzs:   
        if g and (g[0].split()[-1] != d.split()[-1]):      #same speaker
            groups.append(g)
            g = []
    
        g.append(d)
        
        end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=d)[1]
        end = millisec(end)
        if (lastend > end):       #segment engulfed by a previous segment
            groups.append(g)
            g = [] 
        else:
            lastend = end
    if g:
        groups.append(g)
    print(*groups, sep='\n')

    audio = AudioSegment.from_wav(audio_file)
    gidx = -1

    for g in groups:
        start = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[0])[0]
        end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[-1])[1]
        start = millisec(start) #- spacermilli
        end = millisec(end)  #- spacermilli
        gidx += 1
        audio[start:end].export(r"Videos_and_Audio/Audio_Sections/" + str(gidx) + '.wav', format='wav')
        print(f"group {gidx}: {start}--{end}")

    return groups

""" Transcribes the content of the given audio file

This method transcribes the spoken words in the audio files. It uses Open AIs 
Whisper to do this and dumps the transcriptions in the directory. 

The code is copyed more or less directly from: https://github.com/Majdoddin/nlp

Args: 
    audio: the location of an audio file with spoken (english) words
    groups: the output of grouping_diarization()

Returns:
    The transcriptions of the audio files

"""

def transcribe(groups: list):
    print("transcribe")
    device = torch.device("cuda")
    if torch.cuda.is_available():
        print("gpu")
        #device = torch.cuda.device(0)
    #else:
        #dml = torch_directml.device()

    model = whisper.load_model("medium", device = device)    

    for i in range(len(groups)):
        audiof = r"Videos_and_Audio/Audio_Sections/" + str(i) + ".wav"
        result = model.transcribe(audio=audiof, language = "en", word_timestamps= True, verbose = True)

        with open(r"Videos_and_Audio/Transcription_Sections/" + str(i) + ".json", "w") as outfile:
            json.dump(result, outfile, indent = 4)

""" This method combines the two outputs

It more or less appends the speaker information to the Whisper output. 

The code is copyed more or less directly from: https://github.com/Majdoddin/nlp

Args: 
    speakers: the speaker information
    transcription: the transcribed audio in the form Whisper returns

Returns:
    The combination of both. The speaker information is appended to the Whisper-
    given timestamps
"""
def combine_speakers_transcribtion(groups):
    text = []

    gidx = -1
    for g in groups:
        shift = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[0])[0]
        shift = millisec(shift)   #the start time in the original video
        shift = max(shift, 0)

        gidx += 1

        captions = json.load(open(r"Videos_and_Audio/Transcription_Sections/" + str(gidx) + '.json'))['segments']

        if captions:
            speaker = g[0].split()[-1]

        for c in captions:
            start = shift + c['start'] * 1000.0 
            start = start / 1000.0   #time resolution ot youtube is Second.            
            end = (shift + c['end'] * 1000.0) / 1000.0      
            text.append(f'[{timeStr(start)} --> {timeStr(end)}] [{speaker}] {c["text"]}\n')

            #for i, w in enumerate(c['words']):
                #if w == "":
                    #continue
                #start = (shift + w['start']*1000.0) / 1000.0  
                #text.append(f'{w["word"]}')
            text.append('\n')

    with open(r"Videos_and_Audio/Transcription_Sections/capspeaker.txt", "w", encoding='utf-8') as file:
        s = "".join(text)
        file.write(s)
        print(s+'\n')

""" This method summarizes the given textfile using GPT4
"""
def summarize(textfile):
    text  = ""
    
    openai.api_key = openai_key
    openai.Completion.create(
        model = "gpt-4-32k",
        prompt = text + "",
        maxtokens = 200,
        temperature = 0
    )

################# Helper Methods #################
""" Helper Method to convert everything to millisecs

Args:
    timeStr: the String given by getSpeakers()

Return:
    a tidier representation needed in the following steps of computation
"""
def millisec(timeStr: str):
    spl = timeStr.split(":")
    s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2]) )* 1000)
    return s

""" Helper Method to convert the seconds back to the normal time format

Args:
    t: time in seconds

Return:
    a String of in the format [mm]:[ss]:[msms]
"""
def timeStr(t):
  return '{0:02d}:{1:02d}:{2:06.2f}'.format(round(t // 3600),
                                            round(t % 3600 // 60), 
                                            t % 60)


################# Program #################
#print("Making .wav file")
#get_wav("Videos_and_Audio/Test2.mp4")

#print("Finding speakers")
#get_speakers(r"Videos_and_Audio/Test2.mp4.wav")

#print("Grouping speakers")
groups = grouping_diarization(r"diarization.txt", r"Videos_and_Audio/Test2.mp4.wav")

print("Transcribing (This might take a while without CUDA support)")
transcribe(groups) # takes ages without GPU Acceleration even for the 4 min video. In CPU I think it is pretty much 1:1. Transcribing 4 mins takes 4 mins (maybe a bit less)
                    # takes about 20 min for a 40 min video with a GPU (GTX1060)
print("Finalizing Document")
combine_speakers_transcribtion(groups)
