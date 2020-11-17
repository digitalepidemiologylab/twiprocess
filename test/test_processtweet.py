import pytest


def test_extract(process_tweet):
    extract = {
        'id': '1328286627765116929',
        'text': None,
        'in_reply_to_status_id': None,
        'in_reply_to_user_id': None,
        'quoted_user_id': '743827585566654464',
        'quoted_status_id': '1328281820107055104',
        'retweeted_user_id': None,
        'retweeted_status_id': None,
        'created_at': '2020-11-16T10:39:45+00:00',
        'entities.user_mentions': None,
        'user.id': '14177696',
        'user.screen_name': 'marcelsalathe',
        'user.name': 'Marcel Salathé',
        'user.description': 'Private account. Many hats: Prof @EPFL_en, Acad. '
                            'Dir. EPFL Extension School @epfl_exts, '
                            'co-founder @AIcrowdHQ, co-organizer '
                            '@appliedMLdays, YC alumnus',
        'user.timezone': None,
        'user.location': '🇨🇭',
        'user.num_followers': 18066,
        'user.num_following': 1137,
        'user.created_at': '2008-03-19T16:19:03+00:00',
        'user.statuses_count': 134,
        'user.is_verified': True,
        'lang': 'en',
        'is_retweet': False,
        'has_quote': True,
        'is_reply': False,
        'contains_keywords': False,
        'has_media': False,
        'media': {},
        'media_image_urls': []
    }

    assert process_tweet.extract(extract_media=True) == extract

    quoted_extract = {
        'id': '1328281820107055104',
        'text': None,
        'in_reply_to_status_id': None,
        'in_reply_to_user_id': None,
        'quoted_user_id': None,
        'quoted_status_id': None,
        'retweeted_user_id': None,
        'retweeted_status_id': None,
        'created_at': '2020-11-16T10:20:38+00:00',
        'entities.user_mentions': [
            '42676172', '1036304237666492416', '14177696'
        ],
        'user.id': '743827585566654464',
        'user.screen_name': 'marmuel_',
        'user.name': 'Martin Müller',
        'user.description': 'PhD student @EPFL, working on NLP/sentiment '
                            'analysis for Health & Epidemiology',
        'user.timezone': None,
        'user.location': 'Geneva, Switzerland',
        'user.num_followers': 221,
        'user.num_following': 387,
        'user.created_at': '2016-06-17T15:28:10+00:00',
        'user.statuses_count': 219,
        'user.is_verified': False,
        'lang': 'en',
        'is_retweet': False,
        'has_quote': False,
        'is_reply': False,
        'contains_keywords': False,
        'has_media': True,
        'media': {'photo': 1},
        'media_image_urls': ['http://pbs.twimg.com/media/Em70g5PXIAALKOZ.jpg']
    }

    assert process_tweet.quoted_status.extract(extract_media=True) == \
        quoted_extract


def test_media(process_tweet):
    quoted_media = [{
        'id': 1328267786079117300,
        'id_str': '1328267786079117312',
        'indices': [263, 286],
        'media_url': 'http://pbs.twimg.com/media/Em70g5PXIAALKOZ.jpg',
        'media_url_https': 'https://pbs.twimg.com/media/Em70g5PXIAALKOZ.jpg',
        'url': 'https://t.co/JHK8Rg6YNB',
        'display_url': 'pic.twitter.com/JHK8Rg6YNB',
        'expanded_url':
            'https://twitter.com/marmuel_/status/1328281820107055104/photo/1',
        'type': 'photo',
        'sizes': {'thumb': {'w': 150, 'h': 150, 'resize': 'crop'},
        'small': {'w': 680, 'h': 418, 'resize': 'fit'},
        'medium': {'w': 1200, 'h': 737, 'resize': 'fit'},
        'large': {'w': 1214, 'h': 746, 'resize': 'fit'}},
        'ext_alt_text': None
    }]

    assert process_tweet.quoted_status.media == quoted_media
    assert process_tweet.media is None
    assert process_tweet.retweet_or_tweet.media is None
    assert process_tweet.retweet_or_tweet.extended_tweet.media is None
    assert process_tweet.extended_tweet.media is None


def test_retweeted_status(process_tweet):
    assert process_tweet.retweeted_status == type(process_tweet)(None)


def test_retweet_or_tweet(process_tweet):
    assert process_tweet.retweet_or_tweet == process_tweet


def test_parents(process_tweet):
    assert process_tweet.user.parent == process_tweet.extended_tweet.parent
