"""
##############################
Atomic Preprocessing Functions
##############################

For Unicode categories, go to
https://en.wikipedia.org/wiki/Unicode_character_property.
"""

import logging
import re
import os
import html
import unicodedata
import ast

import unidecode
import emoji
# import demoji

from .tokenizer_contractions import CONTRACTIONS

logger = logging.getLogger(__name__)
# demoji.DIRECTORY = '/tmp/.demoji'
# demoji.CACHEPATH = os.path.join(demoji.DIRECTORY, "codes.json")
# demoji.download_codes()

try:
    import spacy
except ImportError:
    logger.warning(
        "Could not import 'spacy'. "
        "'twiprocess.text.tokenize' will not work.")

nlp = None
# try:
#     nlp = spacy.load('en_core_web_sm')
# except OSError:
#     logger.warning(
#         "Could not import 'en_core_web_sm'. "
#         "'twiprocess.text.tokenize' will not work.")
# except NameError:
#     pass

try:
    from bs4 import BeautifulSoup
except ImportError:
    logger.warning(
        "Could not import 'BeautifulSoup' from 'bs4'."
        "'twiprocess.text.parse_html_emoji' will not work.")


# Decorators for composite functions
def check_empty_nonstr(func):
    def wrapper(text, **kwargs):
        if not text:
            return ''
        if not isinstance(text, str):
            text = str(text)
        text = func(text, **kwargs)
        return text

    return wrapper


def drop_multiple_spaces(func):
    def wrapper(text, **kwargs):
        text = func(text, **kwargs)
        # Replace multiple spaces with single space
        return ' '.join(text.split())

    return wrapper


# Functions
def standardize_text(text):
    # Escape HTML symbols
    text = html.unescape(text)
    # Replace control characters by a whitespace
    text = remove_control_characters(text)
    # Normalize by compatibility
    text = normalize(text)
    return text


def parse_html_emoji(text):
    soup = BeautifulSoup(text, 'html.parser')
    spans = soup.find_all('span')
    if len(spans) == 0:
        return text
    while soup.span is not None:
        emoji_bytes = ast.literal_eval(soup.span.attrs['data-emoji-bytes'])
        emoji_unicode = bytes(emoji_bytes).decode()
        soup.span.replace_with(emoji_unicode)
    return soup.text


def separate_hashtags(text):
    text = re.sub(r"#(\w+)#(\w+)", r" #\1 #\2 ", text)
    return text


def replace_mentions(text, filler='@user'):
    """Replaces Twitter @mentions in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    """
    # Positive lookbehinds: https://stackoverflow.com/a/40617321/4949133
    username_regex = re.compile(r'(?:(?<=^)|(?<=[^@\w]))@(\w{1,15})\b')
    # Replace other user handles with the filler
    # Added space to separate the mention from non-space characters behind
    text = re.sub(username_regex, f' {filler} ', text)
    return text


def replace_urls(text, filler='<url>'):
    """Replaces URLs in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    Includes punctuation in websites
    (which is not really a problem, because URLs on Twitter are rendered
    as https://t.co/randomnum).
    The regex doesn't account for what's behind.
    """
    # url_regex = re.compile(
    #     r'((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))')
    twitter_url_regex = re.compile(
        # r'https?://t.co/[A-Za-z0-9]+')
        r'https?://t.co(?:/[0-9a-zA-Z]+)?')
    # Replace other urls by filler
    # Added space to separate the mention from non-space characters behind
    text = re.sub(twitter_url_regex, f' {filler} ', text)
    return text


def replace_emails(text, filler='@email'):
    """Replaces emails in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    """
    email_regex = re.compile(r'[\w\.-]+@[\w\.-]+(\.[\w]+)+')
    # Replace other user handles by filler
    text = re.sub(email_regex, filler, text)
    # Add spaces between, and remove double spaces again
    text = text.replace(filler, f' {filler} ')
    return text


def anonymize_text(text, url_filler='<url>',
                   user_filler='@user', email_filler='@email'):
    """Replaces URLs, mentions and emails in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    """
    text = replace_urls(text, filler=url_filler)
    text = replace_mentions(text, filler=user_filler)
    text = replace_emails(text, filler=email_filler)
    return text


###############################################################################


def remove_control_characters(text):
    """Removes control (C*) Unicode characters."""
    if not isinstance(text, str):
        return text
    # Removes all other control characters and the NULL byte
    # (which causes issues when parsing with pandas)
    return ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')


def asciify(text):
    """Asciify all unicode characters."""
    text = unidecode.unidecode(text)
    return text


def standardize_punctuation(text):
    text = ''.join(
        unidecode.unidecode(c)
        if unicodedata.category(c)[0] == 'P' else c for c in text)
    return text


def remove_punctuation(text):
    """Replaces all Unicode punctuation except dashes (Pd) with whitespaces.
    Potentially induces duplicate whitespaces.
    """
    text = ''.join(
        ' '
        if unicodedata.category(c)[0] == 'P'
        and unicodedata.category(c)[1] != 'd'
        else c for c in text)
    return text


def normalize(text):
    """Normalizes unicode strings by compatibilty (in composed form)."""
    return unicodedata.normalize('NFKC', text)


def remove_emoji(text):
    # """Replaces symbols-other (So) Unicode characters with whitespaces.
    # Potentially induces duplicate whitespaces.
    # """
    # text = ''.join(' ' if unicodedata.category(c) == 'So' else c for c in text)
    # text = demoji.replace(text, ' ')
    emoji.get_emoji_regexp().sub(u' ', text)
    return text


def asciify_emoji(text):
    """Replaces emoji with their descriptions.
    Potentially induces duplicate whitespaces.
    """
    text = emoji.demojize(text)
    # Pad with whitespace
    text = re.sub(r":([\w-]+):", r" :\1: ", text)
    return text


def expand_contractions(text):
    contractions_pattern = re.compile(
        '({})'.format('|'.join(CONTRACTIONS.keys())),
        flags=re.IGNORECASE | re.DOTALL)

    def expand_match(contraction):
        match = contraction.group(0)
        first_char = match[0]
        expanded_contraction = \
            CONTRACTIONS.get(match) \
            if CONTRACTIONS.get(match) \
            else CONTRACTIONS.get(match.lower())
        expanded_contraction = first_char+expanded_contraction[1:]
        return expanded_contraction

    expanded_text = contractions_pattern.sub(expand_match, text)
    expanded_text = re.sub("'", "", expanded_text)
    return expanded_text


def tokenize(text):
    # Create doc
    doc = nlp(text, disable=['parser', 'tagger', 'ner'])
    # Find hashtag indices and merge again (so the # are not lost)
    hashtag_pos = []
    for i, t in enumerate(doc[:-1]):
        if t.text == '#':
            hashtag_pos.append(i)
    with doc.retokenize() as retokenizer:
        for i in hashtag_pos:
            try:
                retokenizer.merge(doc[i:(i+2)])
            except ValueError:
                pass
    return [i for i in doc]
