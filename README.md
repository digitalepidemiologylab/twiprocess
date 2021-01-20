# `twiprocess`: Crowdbreaks Twitter JSON Processing Tool
This is a helper tool to process Twitter data flexibly and efficiently.
The tool contains text preprocessing functions (`twiprocess.atomic`, `twiprocess.standardize`, `twiprocess.preprocess`) as well as classes that handle the Twitter JSON schema (`twiprocess.tweet.Tweet`, `twiprocess.processtweet.ProcessTweet`).

## Installation
```
git clone https://github.com/crowdbreaks/twiprocess.git
cd twiprocess
pip install -e .
```

## Text preprocessing
`twiprocess.atomic` contains atomic preprocessing functions (each does a single thing), which can be combined together. Some of these functions potentially induce multiple whitespaces.

`twiprocess.standardize` contains functions which standardize text before preprocessing it. Standardization can include escaping HTML symbols, normalizing unicode or anonymizing text (replacing Twitter user mentions, URLs or emails with special anonymous words). These functions are built using the atomic functions and decorators, `@check_empty_nonstr` and `@drop_multiple_spaces`. The first one returns an empty string if given a `None` value and converts non-string values to string if possible **before** applying the wrapped function. The second one drops multiple spaces **after** applying the wrapped function.

`twiprocess.preprocess` contains a single preprocessing function with multiple parameters. It is supposed to be used after a standardization function is applied. If `replace_url_with`, `replace_user_with` or `replace_email_with` are not `None`, please make sure that you anonymized your texts using `'<url>'`, `'@user'` and `'@email'` for URLs, user mentions and emails, as the function replaces these perticular values.

## Tweet classes
`twiprocess.tweet.Tweet`
`twiprocess.processtweet.ProcessTweet`
