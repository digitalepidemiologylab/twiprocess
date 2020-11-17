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
        # Backward compatiibility, now (30.10.2020) time_zone
        if 'timezone' in self._user:
            return self._user['timezone']
        return self._user.get('time_zone')


class ExtendedTweet:
    def __init__(self, status, parent):
        self._status = status if status else {}
        self.parent = parent

    # def __eq__(self, other):
    #     if not isinstance(other, ExtendedTweet):
    #         return False
    #     status_eq = self._status == other._status
    #     parent_eq = self.parent == other.parent
    #     return status_eq and parent_eq

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


def standardize_func_default(text):
    return text


class Tweet:
    """Base tweet class."""

    def __init__(
            self,
            status,
            standardize_func=None,
            keywords=None,  # Legacy
            map_data=None,  # localgeocode
            geo_code=None   # localgeocode
    ):
        self._status = status if status else {}
        self.keywords = keywords if keywords else []
        self.standardize_func = \
            getattr(standardize, standardize_func) if standardize_func \
            else standardize_func_default
        self.map_data = map_data
        self.geo_code = geo_code

    # def __eq__(self, other):
    #     if not isinstance(other, Tweet) or not issubclass(type(other), Tweet):
    #         return False
    #     status_eq = self._status == other._status
    #     keywords_eq = self.keywords == other.keywords
    #     standardize_eq = self.standardize_func == other.standardize_func
    #     map_data_eq = self.map_data == other.map_data
    #     geo_code_eq = self.geo_code == other.geo_code
    #     return (
    #         status_eq and keywords_eq and standardize_eq
    #         and map_data_eq and geo_code_eq)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self.__dict__.values())

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
    def text(self):
        if self.retweet_or_tweet.extended_tweet != \
                ExtendedTweet(None, self):
            return self.standardize_func(
                self.retweet_or_tweet.extended_tweet.full_text)
        return self.standardize_func(self.retweet_or_tweet._status.get('text'))

    @property
    @lru_cache(maxsize=1)
    def retweet_or_tweet(self):
        tweet = self
        if self.is_retweet:
            tweet = self.retweeted_status
        return tweet

    # Entities
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

    # Quote
    @property
    def has_quote(self):
        # Used here and in parse_tweets.py
        return 'quoted_status' in self._status

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
        return self._status.get('coordinates', {}).get('coordinates')

    @property
    def place_coordinates(self):
        return self._status.get(
            'place', {}).get('bounding_box', {}).get('coordinates')

    @property
    def place_country_code(self):
        return self._status.get('place', {}).get('country_code')

    @property
    def lang(self):
        return self._status.get('lang')
