from . import atomic


def preprocess(text,
               remove_punctuation=False,
               standardize_punctuation=False,
               asciify_emoji=False,
               remove_emoji=False,
               merge_multiple_users=False,
               merge_multiple_urls=False,
               merge_multiple_emails=False,
               replace_url_with=None,
               replace_user_with=None,
               replace_email_with=None,
               min_num_tokens=0,
               lemmatize=False,
               remove_stop_words=False,
               asciify=False,
               lower_case=False,
               min_num_chars=0):
    """Preprocesses Twitter data.

    Args:
        remove_punctuation (bool): Replace all symbols of punctuation
            unicode category except dashes (Pd). Default: ``False``
        standardize_punctuation (bool): Standardize punctuation.
            Default: ``False``
        asciify_emoji (bool): Asciify emoji. Default: ``False``
        remove_emoji (bool): Remove all characters of symbols-other (So)
            unicode category. Default: ``False``
        merge_multiple_users (bool): Merge multiple stacked occurrences of
            the ``@user`` filler. Default: ``False``
        merge_multiple_urls (bool): Merge multiple stacked occurrences of
            the ``<url>`` filler. Default: ``False``
        merge_multiple_emails (bool): Merge multiple stacked occurrences of
            the ``@email`` filler. Default: ``False``
        replace_url_with (str or None): Replace `<url>` with something else.
            Default: ``None``
        replace_user_with (str or None): Replace `@user` with something else.
            Default: ``None``
        replace_email_with (str or None): Replace `@email` with something else.
            Default: ``None``
        min_num_tokens (int): Minimum number of tokens. Default: 0
        lemmatize (bool): Lemmatize strings. Default: ``False``
        remove_stop_words (bool): Remove stop words. Default: ``False``
        asciify (bool): Asciify accents. Default: ``False``
        lower_case (bool): Lower case. Default: ``True``
        min_num_chars (int): Minimum number of character cutoff. Default: 0

    Returns:
        text (str): Preprocessed text
    """
    # Remove punctuation
    if remove_punctuation:
        text = atomic.remove_punctuation(text)
    # Standardize punctuation
    if standardize_punctuation:
        text = atomic.standardize_punctuation(text)
    # Remove emoji
    if remove_emoji:
        text = atomic.remove_emoji(text)
    # Asciify emoji
    if asciify_emoji:
        text = atomic.asciify_emoji(text)
    # Merge multiple fillers
    if merge_multiple_users:
        atomic.merge_multiple_fillers(text, '@user')
    if merge_multiple_urls:
        atomic.merge_multiple_fillers(text, '<url>')
    if merge_multiple_emails:
        atomic.merge_multiple_fillers(text, '@email')
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
        if remove_stop_words and not lemmatize:
            text = ' '.join([t.text for t in tokens])
        if lemmatize:
            text = ' '.join([t.lemma_ for t in tokens])
    # Asciify
    if asciify:
        text = atomic.asciify(text)
    # Lower case
    if lower_case:
        text = text.lower()
    # Min number of character cutoff
    if min_num_chars > 0:
        if len(text) < min_num_chars:
            return ''
    return text
