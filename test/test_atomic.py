import pytest

from twiprocess.atomic import (standardize_text,
                               parse_html_emoji,
                               separate_hashtags,
                               replace_mentions,
                               replace_urls,
                               replace_emails,
                               anonymize_text,
                               remove_control_characters,
                               asciify,
                               standardize_punctuation,
                               remove_punctuation,
                               normalize,
                               remove_emoji,
                               asciify_emoji,
                               expand_contractions,
                               tokenize)


def test_standardize_text():
    pass


def test_parse_html_emoji():
    pass


def test_separate_hashtags():
    pass


def test_replace_mentions():
    text = 'Hi @Mark! Nice meeting you here!@Jen, what about@you?'
    text = replace_mentions(text)
    assert text == 'Hi  @user ! Nice meeting you here! @user , what about@you?'


def test_replace_urls():
    text = "So there's a link https://t.co/SoMErAnd0M. " \
           "They're all like this in tweet objects."
    text = replace_urls(text)
    assert text == "So there's a link  <url> . " \
                   "They're all like this in tweet objects."


def test_replace_emails():
    text = 'I am a very important person, reach me at vip@guy.me! ' \
           'For business matters:vipbiz@guy.me.'
    text = replace_emails(text)
    assert text == 'I am a very important person, reach me at  @email ! ' \
                   'For business matters: @email .'


def test_anonymize_text():
    text = 'Good samaritan.https://t.co/SaMAr1TaNn-my website. ' \
           'I work for a charity:@charity. Contact me:gs@gmail.com'
    text = anonymize_text(text)
    assert text == 'Good samaritan. <url> -my website. ' \
                   'I work for a charity: @user . Contact me: @email '


###############################################################################


def test_remove_control_characters():
    text = 'Just\n a\t collection\r of\0 control\a characters\f'
    text = remove_control_characters(text)
    assert text == 'Just a collection of control characters'


def test_asciify():
    text = '¿Qué pasa, Олеся, Mr 李? 😉'
    text = asciify(text)
    assert text == '?Que pasa, Olesia, Mr Li ? '


def test_standardize_punctuation():
    text = "‘here’ “are” ´some´ ‵weird‵ ‷punctuations‷; " \
           "they should be standardized… ¡Olé!"
    text2 = standardize_punctuation(text)
    assert text2 == """'here' "are" ´some´ `weird` ```punctuations```; """ \
                    """they should be standardized... !Olé!"""


def test_remove_punctuation():
    text = "Let's eat, Grandma!"
    text = remove_punctuation(text)
    assert text == 'Let s eat  Grandma '


def test_normalize():
    text = "Ä\uFB03n Henry \u2163 🤦🏼\u200d♀️"
    text = normalize(text)
    assert text == 'Äffin Henry IV 🤦🏼\u200d♀️'


def test_remove_emoji():
    text = "here are some emoji 😉🤙🤦🏼‍♀️🦾 that was it"
    text2 = remove_emoji(text)
    assert text2 == """here are some emoji      that was it"""


def test_asciify_emoji():
    text = "here are some emoji 😉🤙🤦🏼‍♀️🦾 that was it"
    text2 = asciify_emoji(text)
    assert text2 == """here are some emoji  :winking_face:  """ \
                    """:call_me_hand:  :woman_facepalming_medium-""" \
                    """light_skin_tone:  :mechanical_arm:  that was it"""


def test_expand_contractions():
    text = "weren't isn't aren't"
    assert expand_contractions(text) == 'were not is not are not'


def test_tokenize():
    pass


if __name__ == "__main__":
    pytest.main()
