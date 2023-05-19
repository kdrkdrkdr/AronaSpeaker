import re
from text.japanese import japanese_to_romaji_with_accent

def japanese_cleaners(text):
    text = japanese_to_romaji_with_accent(text)
    text = re.sub(r'([A-Za-z])$', r'\1.', text)
    return text


def japanese_cleaners2(text):
    text = text.replace('・・・', '…').replace('・', ' ')
    text = japanese_cleaners(text).replace('ts', 'ʦ').replace('...', '…') \
                                    .replace('(', '').replace(')', '') \
                                    .replace('[', '').replace(']', '') \
                                    .replace('*', ' ').replace('{', '').replace('}', '')
    return text
