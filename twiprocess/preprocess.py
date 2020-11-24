from . import atomic


# def add_function(condition, func_to_add):
#     def decorator(main_func):
#         def wrapper(text):
#             text = func_to_add(text)
#             text = main_func(text)
#             return text
#         return wrapper
#     return decorator if condition else lambda x: x


# def get_preprocess_func(
#         min_num_tokens=0,
#         min_num_chars=0,
#         lower_case=False,
#         asciify=False,
#         remove_punctuation=False,
#         asciify_emoji=False,
#         remove_emoji=False,
#         replace_url_with=None,
#         replace_user_with=None,
#         replace_email_with=None,
#         lemmatize=False,
#         remove_stop_words=False
# ):
#     def spacy_stuff(text):
#         tokens = atomic.tokenize(text)
#         # Ignore everything below min_num_tokens
#         if min_num_tokens > 0:
#             num_tokens = sum((
#                 1 for t in tokens
#                 if t.is_alpha and
#                 not t.is_punct and
#                 t.text.strip()
#                 not in [replace_user_with, replace_url_with]))
#             if num_tokens < min_num_tokens:
#                 return ''
#         # Remove stop words
#         if remove_stop_words:
#             tokens = [t for t in tokens if not t.is_stop]
#         # Merge
#         if (remove_stop_words) and not lemmatize:
#             text = ' '.join([t.text for t in tokens])
#         if lemmatize:
#             text = ' '.join([t.lemma_ for t in tokens])
#         return text

#     @add_function(asciify, atomic.asciify)
#     @add_function(remove_punctuation, atomic.remove_punctuation)
#     @add_function(remove_emoji, atomic.remove_emoji)
#     @add_function(asciify_emoji, atomic.asciify_emoji)
#     @add_function(
#         replace_url_with, lambda x: x.replace('<url>', replace_url_with))
#     @add_function(
#         replace_user_with, lambda x: x.replace('@user', replace_url_with))
#     @add_function(
#         replace_email_with, lambda x: x.replace('@email', replace_url_with))
#     @add_function(lower_case, lambda x: x.lower())
#     @add_function(True, lambda x: ' '.join(x.split()))
#     @add_function(min_num_chars, lambda x: '' if len(x) < min_num_chars else x)
#     @add_function(
#         min_num_tokens > 0 or lemmatize or remove_stop_words,
#         spacy_stuff)
#     def preprocess_func(text):
#         return text

#     return preprocess_func


def preprocess(text,
               min_num_tokens=0,
               min_num_chars=0,
               lower_case=False,
               asciify=False,
               remove_punctuation=False,
               standardize_punctuation=False,
               asciify_emoji=False,
               remove_emoji=False,
               replace_url_with=None,
               replace_user_with=None,
               replace_email_with=None,
               lemmatize=False,
               remove_stop_words=False,
               **kwargs):
    """Preprocesses Twitter data.

    Args:
        min_num_tokens (int): Minimum number of tokens. Default: 0
        min_num_chars (int): Minimum number of character cutoff. Default: 0
        lower_case (bool): Lower case. Default: ``True``
        asciify (bool): Asciify accents. Default: ``False``
        remove_punctuation (bool): Replace all symbols of punctuation
            unicode category except dashes (Pd). Default: ``False``
        asciify_emoji (bool): Asciify emoji. Default: ``False``
        remove_emoji (bool): Remove all characters of symbols-other (So)
            unicode category. Default: ``False``
        replace_url_with (str or None): Replace `<url>` with something else.
            Default: ``None``
        replace_user_with (str or None): Replace `@user` with something else.
            Default: ``None``
        replace_email_with (str or None): Replace `@email` with something else.
            Default: ``None``
        lemmatize (bool): Lemmatize strings. Default: ``False``
        remove_stop_words (bool): Remove stop words. Default: ``False``

    Returns:
        text (str): Preprocessed text
    """
    # Asciify
    if asciify:
        text = atomic.asciify(text)
    # Remove punctuation
    if remove_punctuation:
        text = atomic.remove_punctuation(text)
    if standardize_punctuation:
        text = atomic.standardize_punctuation(text)
    # Remove emoji
    if remove_emoji:
        text = atomic.remove_emoji(text)
    # Asciify emoji
    if asciify_emoji:
        text = atomic.asciify_emoji(text)
    # Replace urls/users/emails with something else
    if replace_url_with is not None:
        text = text.replace('<url>', replace_url_with)
    if replace_user_with is not None:
        text = text.replace('@user', replace_user_with)
    if replace_email_with is not None:
        text = text.replace('@email', replace_email_with)
    # Remove potentially induced duplicate whitespaces
    text = ' '.join(text.split())
    if (min_num_tokens > 0 or lemmatize or remove_stop_words) and atomic.nlp:
        tokens = atomic.tokenize(text)
        # Ignore everything below min_num_tokens
        if min_num_tokens > 0:
            num_tokens = sum((
                1 for t in tokens
                if t.is_alpha and
                not t.is_punct and
                t.text.strip()
                not in [replace_user_with, replace_url_with]))
            if num_tokens < min_num_tokens:
                return ''
        # Remove stop words
        if remove_stop_words:
            tokens = [t for t in tokens if not t.is_stop]
        # Merge
        if (remove_stop_words) and not lemmatize:
            text = ' '.join([t.text for t in tokens])
        if lemmatize:
            text = ' '.join([t.lemma_ for t in tokens])
    # Lower case
    if lower_case:
        text = text.lower()
    # Min number of character cutoff
    if min_num_chars > 0:
        if len(text) < min_num_chars:
            return ''
    return text
