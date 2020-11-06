import logging
from functools import lru_cache

from . import standardize

logger = logging.getLogger(__name__)


class User:
    def __init__(self, user, parent):
        self._user = user
        self.parent = parent

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

    # Text
    @property
    def full_text(self):
        return self._status.get('full_text')

    # Extended entities
    @property
    def media(self):
        # https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/overview/intro-to-tweet-json
        return self._status.get('extended_entities', {}).get('media', [])


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
            else lambda text: text
        self.map_data = map_data
        self.geo_code = geo_code

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
        if self.retweet_or_tweet.extended_tweet:
            return self.standardize_func(
                self.retweet_or_tweet.extended_tweet.full_text)
        return self.standardize_func(self.retweet_or_tweet._status.get('text'))

    @property
    @lru_cache(maxsize=1)
    def retweet_or_tweet(self):
        tweet = self
        if self.retweeted_status:
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
            'extended_entities', {}).get('media', [])

    # Extended tweet
    @property
    def extended_tweet(self):
        return ExtendedTweet(self._status.get('extended_tweet'), parent=self)

    # Retweet
    @property
    def is_retweet(self):
        # Used here and in parse_tweets.py
        return 'retweeted_status' in self._status

    @property
    def retweeted_status(self):
        return Tweet(self._status.get('retweeted_status'))

    # Quote
    @property
    def has_quote(self):
        # Used here and in parse_tweets.py
        return 'quoted_status' in self._status

    @property
    def quoted_status(self):
        return Tweet(self._status.get('quoted_status'))

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
