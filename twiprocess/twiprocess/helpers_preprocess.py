import os
import logging
import pandas as pd

from .preprocess import (_asciify,
                         _remove_punctuation,
                         _asciify_emoji,
                         _remove_emoji,
                         _tokenize)

logger = logging.getLogger(__name__)


def preprocess_data(data_path, preprocessing_config):
    """Reads and preprocesses data.

    Args:
        data_path (str): Path to `.csv` file with two columns,
            ``'text'`` and ``'label'``
        preprocessing_config (dict): Config with args for
            ``preprocess_fasttext()``

    Returns:
        df (pandas DataFrame): Dataframe with preprocessed ``'text'`` field
    """
    # Read data
    logger.info(f'Reading data from {data_path}...')
    df = pd.read_csv(
        data_path,
        usecols=['text', 'label'], dtype={'text': str, 'label': str})
    # Drop nans in 'text' or 'label'
    num_loaded = len(df)
    df.dropna(subset=['text', 'label'], inplace=True)
    print('Input data')
    print(df.head())
    # Preprocess data
    try:
        standardize_func_name = preprocessing_config['standardize_func_name']
        del preprocessing_config['standardize_func_name']
    except KeyError:
        standardize_func_name = None
    if standardize_func_name is not None:
        logger.info('Standardizing data...')
        standardize_func = getattr(
            __import__(
                'txcl.utils.standardize',
                fromlist=[standardize_func_name]),
            standardize_func_name)
        df['text'] = df.text.apply(standardize_func)
        print('\nStandardized data')
        print(df.head())
    try:
        preprocess_func_name = preprocessing_config['preprocess_func_name']
        del preprocessing_config['preprocess_func_name']
    except KeyError:
        preprocess_func_name = None
    if preprocess_func_name is not None and preprocessing_config != {}:
        logger.info('Preprocessing data...')
        df['text'] = df.text.apply(
            preprocess_func_name, **preprocessing_config)
        print('\nPreprocessed data')
        print(df.head())
    # Drop empty strings in 'text'
    df = df[df['text'] != '']
    num_filtered = num_loaded - len(df)
    if num_filtered > 0:
        logger.warning(
            f'Filtered out {num_filtered:,} from {num_loaded:,} samples!')
    return df


def prepare_data(data_path, output_dir_path,
                 preprocessing_config):
    """Prepares data for FastText training.

    First, preprocesses data with ``preprocess_data``. Second, formats
    data for FastText.

    Args:
        data_path (str): Path to `.csv` file with two columns,
            ``text`` and ``label``
        output_dir_path (str): Path to the output folder
        preprocessing_config (dict): Preprocessing config

    Returns:
        output_file_path (str): Path to temporary file with
            preprocessed formatted data
    """
    paths = []
    # Preprocess data
    df = preprocess_data(data_path, preprocessing_config)
    # Write data
    # Create paths
    output_file_path = os.path.join(
        output_dir_path, os.path.basename(data_path))
    paths.append(output_file_path)
    # Write
    df.to_csv(
        output_file_path,
        index=False, header=True)
    return paths


def preprocess_twitter(text,
                       min_num_tokens=0,
                       min_num_chars=0,
                       lower_case=False,
                       asciify=False,
                       remove_punctuation=False,
                       asciify_emoji=False,
                       remove_emoji=False,
                       replace_url_with=None,
                       replace_user_with=None,
                       replace_email_with=None,
                       lemmatize=False,
                       remove_stop_words=False):
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
        text = _asciify(text)
    # Remove punctuation
    if remove_punctuation:
        text = _remove_punctuation(text)
    # Remove emoji
    if remove_emoji:
        text = _remove_emoji(text)
    # Asciify emoji
    if asciify_emoji:
        text = _asciify_emoji(text)
    # Replace urls/users/emails with something else
    if replace_url_with is not None:
        text = text.replace('<url>', replace_url_with)
    if replace_user_with is not None:
        text = text.replace('@user', replace_user_with)
    if replace_email_with is not None:
        text = text.replace('@email', replace_email_with)
    # Remove potentially induced duplicate whitespaces
    text = ' '.join(text.split())
    if min_num_tokens > 0 or lemmatize or remove_stop_words:
        tokens = _tokenize(text)
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
        if (remove_stop_words or remove_punctuation) and not lemmatize:
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
