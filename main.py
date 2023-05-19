import io
import os
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep

from llm import AnswerChatGPT, AnswerBard
from tts import tts_arona
import shutil



start_word = ['アロナ', 'アロンア', 'アロンあ', 'あるな', 'アルナ', '아로나', '아론아', '아르나', 'Arona', 'arona']


def isStartWordCalled(string: str):
    string = string.replace('.', '').replace('?', '').replace('!', '').replace(' ', '')
    for sw in start_word:
        if string[-len(sw):] == sw:
            return True
    return False



def stt_arona():
    energy_threshold = 1000
    record_timeout = 2
    phrase_timeout = 3
    
    phrase_time = None
    last_sample = bytes()
    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = energy_threshold
    recorder.dynamic_energy_threshold = False
    
    source = sr.Microphone(sample_rate=16000)
    audio_model = whisper.load_model("medium", download_root='pretrained_model/whisper/')

    temp_file = NamedTemporaryFile().name
    transcription = ['']
    
    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio:sr.AudioData) -> None:
        data = audio.get_raw_data()
        data_queue.put(data)

    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    print("Whisper Model Loaded!\n")

    isCalledArona = False

    while True:
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                phrase_complete = False
                
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                phrase_time = now

                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                result = audio_model.transcribe(
                    temp_file,
                    fp16=torch.cuda.is_available(),
                    # language="Japanese",
                )
                text = result['text'].strip()
                print(f'isCalledArona={isCalledArona}',)
                if (result['language'] == 'nn') or (not text):
                    continue

                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text
                    
                print(text)
                
                if transcription != '':
                    if isCalledArona:
                        msg = AnswerBard(transcription[-1])
                        tts_arona(msg)
                        isCalledArona = False
                        continue
                    
                    if isStartWordCalled(transcription[-1]):
                        tts_arona("はい、先生")
                        sleep(0.25)
                        isCalledArona = True
                        print("아로나를 호출했어요! 지금 질문하세요!")
                        continue

                    isCalledArona = False

        except KeyboardInterrupt:
            break


    

if __name__ == "__main__":
    stt_arona()