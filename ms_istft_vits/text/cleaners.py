import re
from ms_istft_vits.text.japanese import japanese_to_romaji_with_accent
from ms_istft_vits.text.korean import latin_to_hangul, number_to_hangul, divide_hangul
from ms_istft_vits.text.symbols import symbols


_cleaner_cleans = re.compile('['+'^'.join(symbols)+']')


def japanese_cleaners(text):
    text = japanese_to_romaji_with_accent(text)
    text = re.sub(r'([A-Za-z])$', r'\1.', text)
    return text


def japanese_cleaners2(text):
    text = japanese_cleaners(text).replace('ts', 'ʦ').replace('...', '…')
    text = ''.join(_cleaner_cleans.findall(text))#.replace(' ', '')
    return text


def korean_cleaners(text):
    '''Pipeline for Korean text'''
    text = latin_to_hangul(text)
    text = number_to_hangul(text)
    text = divide_hangul(text)
    text = re.sub(r'([\u3131-\u3163])$', r'\1.', text)
    return text