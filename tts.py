# import sengiri
import re
import torch
from scipy.io.wavfile import write
import winsound
import ko2kata

tts_model = 'ms_istft_vits'
# tts_model = 'vits'

if tts_model == 'ms_istft_vits':
    SPEECH_SPEED = 0.98
    from ms_istft_vits import commons
    from ms_istft_vits import utils
    from ms_istft_vits.models import SynthesizerTrn
    from ms_istft_vits.text.symbols import symbols
    from ms_istft_vits.text import text_to_sequence
else:
    SPEECH_SPEED = 1
    from vits import commons
    from vits import utils
    from vits.models import SynthesizerTrn
    from vits.text.symbols import symbols
    from vits.text import text_to_sequence


def get_text(text, hps):
    text_norm = text_to_sequence(text, hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = torch.LongTensor(text_norm)
    return text_norm


hps = utils.get_hparams_from_file(f"pretrained_model/arona_{tts_model}_config.json")
net_g = SynthesizerTrn(
    len(symbols),
    hps.data.filter_length // 2 + 1,
    hps.train.segment_size // hps.data.hop_length,
    n_speakers=hps.data.n_speakers,
    **hps.model).cuda()
_ = net_g.eval()

_ = utils.load_checkpoint(f"pretrained_model/arona_{tts_model}.pth", net_g, None)

def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


# TODO: sengiri로 문장이 더 잘 잘리도록 이상한 문자는 제거해야함.
def tts_arona(content: str, isKor=False):
    content = re.sub('[\s・·+]', ' ', content).replace('。。', '。').strip()
    BRACKETS = '[｢「(（\[［【『〈《〔｛{«‹〖〘〚｣」)）\]］】』〉》〕｝}»›〗〙〛]'
    content = re.sub(BRACKETS, '', content)

    sent_lst = [content]#sengiri.tokenize(content)
    for text in [' '.join(s) for s in list_chunk(lst=sent_lst, n=1)]: # n문장씩 끊어서 추론할거임. (너무 긴 문장을 한번에 합성하면 GPU 너무 잡아먹는다.)
        print('아로나 Speech: ', text)
        if isKor:
            print("isKOR = True")
            text = text.replace(' ', '_')
            text = ko2kata.korean2katakana(text).replace('__', '_')
            

        stn_tst = get_text(text, hps)
        with torch.no_grad():
            x_tst = stn_tst.cuda().unsqueeze(0)
            x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).cuda()
            audio = net_g.infer(x_tst, x_tst_lengths, noise_scale=.667, noise_scale_w=0.8, length_scale=1/SPEECH_SPEED)[0][0,0].data.cpu().float().numpy()
            write('sound/infer.wav', hps.data.sampling_rate, audio)
            winsound.PlaySound('sound/infer.wav', winsound.SND_FILENAME)


tts_arona(open('test.txt', 'r', encoding='utf-8').read(), True)
# arona_ms_istft_vits.pth