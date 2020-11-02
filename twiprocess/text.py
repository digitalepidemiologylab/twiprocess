"""
Text processing helpers
=====================

For Unicode categories, go to
https://en.wikipedia.org/wiki/Unicode_character_property.
"""

import logging
import re
import html
import unicodedata

import unidecode
import emoji

logger = logging.getLogger(__name__)

try:
    import spacy
except ImportError:
    logger.warning("Could not import 'spacy'. 'tokenize' won't work.")

nlp = spacy.load('en_core_web_sm')


def separate_hashtags(text):
    text = re.sub(r"#(\w+)#(\w+)", r" #\1 #\2 ", text)
    return text


def standardize_text(text):
    if not text:
        return ''
    if not isinstance(text, str):
        text = str(text)
    # Escape HTML symbols
    text = html.unescape(text)
    # Replace control characters by a whitespace
    text = remove_control_characters(text)
    # Normalize by compatibility
    text = normalize(text)
    return text


def replace_mentions(text, filler='@user'):
    """Replaces Twitter @mentions in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    """
    # Positive lookbehinds: https://stackoverflow.com/a/40617321/4949133
    username_regex = re.compile(r'(?:(?<=^)|(?<=[^@\w]))@(\w{1,15})\b')
    # Replace other user handles with the filler
    # Added space to separate the mention from non-space characters behind
    text = re.sub(username_regex, f' {filler}', text)
    return text


def replace_urls(text, filler='<url>'):
    """Replaces URLs in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    Includes punctuation in websites
    (which is not really a problem, because URLs on Twitter are rendered
    as https://t.co/randomnum).
    The regex doesn't account for what's behind.
    """
    url_regex = re.compile(
        r'((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))')
    # Replace other urls by filler
    # Added space to separate the mention from non-space characters behind
    text = re.sub(url_regex, f' {filler}', text)
    return text


def replace_emails(text, filler='@email'):
    """Replaces emails in text with `f' {filler}'`.
    Potentially induces duplicate whitespaces.
    """
    email_regex = re.compile(r'[\w\.-]+@[\w\.-]+(\.[\w]+)+')
    # Replace other user handles by filler
    text = re.sub(email_regex, filler, text)
    # Add spaces between, and remove double spaces again
    text = text.replace(filler, f' {filler}')
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
    """Replaces symbols-other (So) Unicode characters with whitespaces.
    Potentially induces duplicate whitespaces.
    """
    text = ''.join(' ' if unicodedata.category(c) == 'So' else c for c in text)
    return text


def asciify_emoji(text):
    """Replaces emoji with their descriptions.
    Potentially induces duplicate whitespaces.
    """
    text = emoji.demojize(text)
    # Pad with whitespace
    text = re.sub(r":(\w+):", r" :\1: ", text)
    return text


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
