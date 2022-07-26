"""
##################
Base Tweet Classes
##################

***********
Usage Notes
***********

Properties
==========

Pay attention that properties that return sub-objects
(e.g. ``Tweet().retweet_or_tweet``, ``Tweet().extended_tweet``,
``Tweet().user``) do not return ``None`` if empty, but an empty instance of
the corresponding class (e.g. ``Tweet``, ``ExtendedTweet``, ``User``).

Given this, please don't use these properties to confirm existence of
a sub-object in ``if`` statements such as
```
if tweet.extended_tweet:
    do sth
```

Instead, go for
```
if tweet.has_extended:
    do sth
```

This is done to simplify further attributions on these new objects.
E.g. you can go ``tweet.retweet_or_tweet.extended_tweet.media``.

The classes below use the ``dict`` ``get()`` method to do that, so to
not trigger ``TypeError``s in case of ``None`` objects, it was decided
to return empty sub-objects instead of ``None``.

Comparisons
===========
You can compare ``Tweet``, ``ExtendedTweet`` and ``User`` objects.
``Tweet`` objects can be compared to the child classes objects as long as
they do not introduce their own attributes (comparison is done on object's
``__dict__`` attribute).
"""

import logging
from functools import lru_cache

from . import standardize

logger = logging.getLogger(__name__)


class User:
    def __init__(self, user, parent):
        self._user = user
        self.parent = parent

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.__dict__.values())

    @property
    def id(self):
        return self._user.get('id_str')

    @property
    def name(self):
        return self._user.get('name')

    @property
    def screen_name(self):
        return self._user.get('screen_name')

    @property
    def location(self):
        return self._user.get('location')

    @property
    def description(self):
        return self.parent.standardize_func(self._user.get('description'))

    @property
    def verified(self):
        return self._user.get('verified')

    @property
    def followers_count(self):
        return self._user.get('followers_count')

    @property
    def friends_count(self):
        return self._user.get('friends_count')

    @property
    def statuses_count(self):
        return self._user.get('statuses_count')

    @property
    def created_at(self):
        return self._user.get('created_at')

    @property
    def time_zone(self):
        # 19.01.2021 Deprecated
        # Backward compatiibility, now (30.10.2020) time_zone
        if 'timezone' in self._user:
            return self._user['timezone']
        return self._user.get('time_zone')

    @property
    def lang(self):
        # 19.01.2021 Deprecated
        return self._user.get('lang')


class ExtendedTweet:
    def __init__(self, status, parent):
        self._status = status if status else {}
        self.parent = parent

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.__dict__.values())

    # Text
    @property
    def full_text(self):
        return self._status.get('full_text')

    # Extended entities
    @property
    def media(self):
        # https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/overview/intro-to-tweet-json
        return self._status.get('extended_entities', {}).get('media')


class Place:
    def __init__(self, status, parent):
        self._status = status if status else {}
        self.parent = parent

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.__dict__.values())

    @property
    def coordinates(self):
        bounding_box = self._status.get('bounding_box', {})
        if not isinstance(bounding_box, dict):
            print(self._status)
            return {}
        else:
            return bounding_box.get('coordinates')

    @property
    def country_code(self):
        return self._status.get('country_code')

    @property
    def place_type(self):
        return self._status.get('place_type')


def standardize_func_default(text):
    return text


class Tweet:
    """Base tweet class."""

    def __init__(
            self,
            status,
            standardize_func=None,
            keywords=None,  # Legacy
            map_data=None,  # local-geocode
            geo_code=None   # local-geocode
    ):
        self._status = status if status else {}
        self.keywords = keywords if keywords else []
        self.standardize_func = \
            getattr(standardize, standardize_func) if standardize_func \
            else standardize_func_default
        self.map_data = map_data
        self.geo_code = geo_code

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.__dict__.values())

    # Streamer info
    @property
    def project(self):
        return self._status.get('project')

    @property
    def matching_keywords(self):
        return self._status.get('matching_keywords', [])

    # ID
    @property
    def id(self):
        return self._status.get('id_str')

    # Created at
    @property
    def created_at(self):
        return self._status.get('created_at')

    # User
    @property
    def user(self):
        return User(self._status.get('user', {}), parent=self)

    # Text
    @property
    @lru_cache(maxsize=1)
    def text(self, standardize_func_name=None):
        standardize_func = self.standardize_func
        if standardize_func_name != None:
            standardize_func = getattr(standardize, standardize_func_name)
        if self.retweet_or_tweet.extended_tweet._status != {}:
            return standardize_func(
                self.retweet_or_tweet.extended_tweet.full_text)
        elif 'full_text' in self.retweet_or_tweet._status:
            field = 'full_text'
        else:
            field = 'text'
        return standardize_func(self.retweet_or_tweet._status.get(field))

    @property
    @lru_cache(maxsize=1)
    def retweet_or_tweet(self):
        tweet = self
        if self.is_retweet:
            tweet = self.retweeted_status
        return tweet

    # Entities
    @property
    def hashtags(self):
        hashtags = self._status.get('entities', {}).get('hashtags', [])
        return [h['text'] for h in hashtags]

    @property
    def user_mentions(self):
        return self._status.get('entities', {}).get('user_mentions', [])

    @property
    def urls(self):
        return self._status.get('entities', {}).get('urls', [])

    # Extended entities
    @property
    @lru_cache(maxsize=1)
    def media(self):
        # https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/overview/intro-to-tweet-json
        if self.retweet_or_tweet.extended_tweet.media:
            return self.retweet_or_tweet.extended_tweet.media
        return self.retweet_or_tweet._status.get(
            'extended_entities', {}).get('media')

    # Extended tweet
    @property
    def has_extended(self):
        return 'extended_tweet' in self._status

    @property
    def extended_tweet(self):
        return ExtendedTweet(
            self._status.get('extended_tweet'), parent=self)

    # Retweet
    @property
    def is_retweet(self):
        # Used here and in parse_tweets.py
        return 'retweeted_status' in self._status

    @property
    def retweeted_status(self):
        return type(self)(self._status.get('retweeted_status'))

    @property
    def retweet_count(self):
        return self._status.get('retweet_count')

    # Quote
    @property
    def has_quote(self):
        # Used here and in parse_tweets.py
        return 'quoted_status' in self._status and not self.is_retweet

    @property
    def quoted_status(self):
        return type(self)(self._status.get('quoted_status'))

    # Reply
    @property
    def is_reply(self):
        # Used here and in parse_tweets.py
        return self._status.get('in_reply_to_status_id_str') is not None

    @property
    def replied_status_id(self):
        # Used in parse_tweets.py
        return self._status.get('in_reply_to_status_id_str')

    @property
    def replied_user_id(self):
        return self._status.get('in_reply_to_user_id_str')

    # Location
    @property
    def coordinates(self):
        coordinates = self._status.get('coordinates', {})
        return coordinates.get('coordinates') if coordinates else None

    @property
    def place(self):
        return Place(
            self._status.get('place'), parent=self)

    @property
    def lang(self):
        return self._status.get('lang')
