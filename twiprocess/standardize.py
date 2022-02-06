from .atomic import (check_empty_nonstr,
                     drop_multiple_spaces,
                     parse_html_emoji,
                     separate_hashtags,
                     standardize_text,
                     anonymize_text)


@check_empty_nonstr
@drop_multiple_spaces
def standardize(text):
    # Standardize text
    text = standardize_text(text)
    return text


@check_empty_nonstr
@drop_multiple_spaces
def standardize_html(text):
    # Parse HTML emoji
    text = parse_html_emoji(text)
    # Separate hashtags
    text = separate_hashtags(text)
    # Standardize text
    text = standardize_text(text)
    return text


@check_empty_nonstr
@drop_multiple_spaces
def standardize_anonymize(text):
    # Standardize text
    text = standardize_text(text)
    # Anonymize
    text = anonymize_text(text)
    return text


@check_empty_nonstr
@drop_multiple_spaces
def standardize_anonymize_html(text):
    # Parse HTML emoji
    text = parse_html_emoji(text)
    # Separate hashtags
    text = separate_hashtags(text)
    # Standardize text
    text = standardize_text(text)
    # Anonymize
    text = anonymize_text(text)
    return text

@check_empty_nonstr
@drop_multiple_spaces
def separate_standardize_anonymize(text):
    # Separate hashtags
    text = separate_hashtags(text)
    # Standardize text
    text = standardize_text(text)
    # Anonymize
    text = anonymize_text(text)
    return text
