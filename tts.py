import re
import torch
import commons
import utils
from models import SynthesizerTrn
from text.symbols import symbols
from text import text_to_sequence

from scipy.io.wavfile import write
import winsound


def get_text(text, hps):
    text = re.sub('[\s+]', ' ', text)
    text_norm = text_to_sequence(text, hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = torch.LongTensor(text_norm)
    return text_norm


# Inference
hps = utils.get_hparams_from_file(f"pretrained_model/vits/arona_config.json")
net_g = SynthesizerTrn(
    len(symbols),
    hps.data.filter_length // 2 + 1,
    hps.train.segment_size // hps.data.hop_length,
    n_speakers=hps.data.n_speakers,
    **hps.model).cuda()
_ = net_g.eval()

_ = utils.load_checkpoint(f"pretrained_model/vits/arona_vits.pth", net_g, None)

speed = 1

def tts_arona(text):
    stn_tst = get_text(text, hps)
    with torch.no_grad():
        x_tst = stn_tst.cuda().unsqueeze(0)
        x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).cuda()
        audio = net_g.infer(x_tst, x_tst_lengths, noise_scale=.667, noise_scale_w=0.8, length_scale=1/speed)[0][0,0].data.cpu().float().numpy()
    write('infer.wav', hps.data.sampling_rate, audio)
    winsound.PlaySound('infer.wav', winsound.SND_FILENAME)