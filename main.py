import io
import speech_recognition as sr
from faster_whisper import WhisperModel

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep

from llm import LLM
from tts import tts_arona
from papagopy import Papagopy

p = Papagopy()

start_word = ['アロナ', 'アロンア', 'アロンあ', 'あるな', 'アルナ', '아로나', '아론아', '아르나', '아레나', 'Arona', 'arona']


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
    audio_model = WhisperModel(
        model_size_or_path='large-v2',
        device='cuda',
        compute_type='float16',
    )

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

                segments, info = audio_model.transcribe(
                    temp_file,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=500
                    ),
                )
                text = ' '.join([s.text for s in segments]).strip()
                language = info.language

                print(f'isCalledArona={isCalledArona}',)
                if not text:
                    continue

                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text
                    
                print(f"text = '{text}'")
                
                if transcription != '':
                    if isCalledArona: # if True 로 바꾸고 if isStartWordCalled 부분 주석처리하면 그냥 아로나와 대화하는 것.
                        msg = LLM(transcription[-1])
                        
                        if language != 'ja':
                            msg = p.translate(msg, 'ja')
                            
                        print(msg)
                        tts_arona(msg)
                        print("아로나가 대답을 모두 했어요!")
                        isCalledArona = False
                        continue
                    
                    if isStartWordCalled(transcription[-1]):
                        tts_arona("はい、先生")
                        # sleep(0.25)
                        isCalledArona = True
                        print("아로나를 호출했어요! 지금 질문하세요!")
                        continue

                    isCalledArona = False

        except KeyboardInterrupt:
            break


    

if __name__ == "__main__":
    stt_arona()