"""
###############################
A Class for Tweet Preprocessing
###############################
"""

import logging
from collections import defaultdict
from functools import lru_cache
from datetime import timezone
from dateutil.parser import parse

import shapely.geometry

from .tweet import Tweet
from .atomic import anonymize_text

logger = logging.getLogger(__name__)

try:
    import spacy
except ImportError:
    logger.warning(
        "Could not import 'spacy', "
        "'twiprocess.tweets.get_token_count' will not work.")

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logger.warning(
        "Could not import 'en_core_web_sm', "
        "'twiprocess.tweets.get_token_count' will not work.")
except NameError:
    pass


class ProcessTweet(Tweet):
    """Wrapper class for processing functions."""

    def extract(self, extract_media=False, extract_geo=False):
        """Extracts the relevant info from an S3 tweet."""
        geo_obj = self.add_region_info(self.geo_info) if extract_geo else {}
        media = self.media_info if extract_media else {}
        return {
            'id': self.id,
            'text': self.text,
            'in_reply_to_status_id': self.replied_status_id,
            'in_reply_to_user_id': self.replied_user_id,
            'quoted_user_id': self.quoted_status.user.id,
            'quoted_status_id': self.quoted_status.id,
            'retweeted_user_id': self.retweeted_status.user.id,
            'retweeted_status_id': self.retweeted_status.id,
            'created_at': parse(self.created_at).isoformat(),
            'entities.user_mentions': self.user_mentions_ids,
            'user.id': self.user.id,
            'user.screen_name': self.user.screen_name,
            'user.name': self.user.name,
            'user.description': self.user.description,
            'user.timezone': self.user.time_zone,
            'user.location': self.user.location,
            'user.num_followers': self.user.followers_count,
            'user.num_following': self.user.friends_count,
            'user.created_at': parse(self.user.created_at).isoformat(),
            'user.statuses_count': self.user.statuses_count,
            'user.is_verified': self.user.verified,
            'lang': self.lang,
            'is_retweet': self.is_retweet,
            'has_quote': self.has_quote,
            'is_reply': self.is_reply,
            'contains_keywords':
                True
                if self._status.get('matching_keywords')
                else self.contains_keywords(),
            **geo_obj,
            **media
        }

    def extract_es(self, extract_geo=False):
        geo_obj = self.geo_info if extract_geo else {}
        if geo_obj['latitude'] and geo_obj['longitude']:
            geo_obj['coordinates'] = {
                'lat': geo_obj.pop('latitude'),
                'lon': geo_obj.pop('longitude')
            }
        else:
            geo_obj = None

        user = {
            'id': self.user.id,
            'name': self.user.name,
            'screen_name': self.user.screen_name,
            'location': self.user.location,
            'description': self.user.description
        }
        user = {k: v for k, v in user.items() if v is not None}

        es_obj = {
            'created_at': parse(
                self.created_at
            ).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'id': self.id,
            'text': self.text,
            'in_reply_to_user_id': self.replied_user_id,
            'retweeted_user_id': self.retweeted_status.user.id,
            'quoted_user_id': self.quoted_status.user.id,
            'user': user,
            'geo_info': geo_obj,
            'hashtags': self.hashtags if self.hashtags != [] else None,
            'has_quote': self.has_quote,
            'is_retweet': self.is_retweet,
            'lang': self.lang,
            'project': self.project,
            'matching_keywords':
                self.matching_keywords
                if self.matching_keywords != [] else None
        }

        es_obj = {
            k: v for k, v in es_obj.items()
            if v is not None and v is not False}

        return es_obj

    @property
    def user_mentions_ids(self):
        """Doesn't get mentions from ``retweeted_status``es
        within the original tweet.
        """
        user_mentions = [
            mention['id_str']
            for mention in self.user_mentions]
        if user_mentions == []:
            return None
        return user_mentions

    @property
    def geo_info(self):
        """
        Tries to infer different types of geoenrichment from tweet
        (ProcessTweet object).
        Returns:
            geo_obj (dict): A dictionary with the following keys:
                - geo_type (int)
                - longitude (float)
                - latitude (float)
                - country_code (str)
                - location_type (str)
                - geocode (str)
        """
        def get_country_code_by_coords(longitude, latitude):
            if self.map_data:
                coordinates = shapely.geometry.point.Point(longitude, latitude)
                within = self.map_data.geometry.apply(coordinates.within)
                if sum(within) > 0:
                    return self.map_data[within].iloc[0].ISO_A2
                else:
                    dist = self.map_data.geometry.apply(
                        lambda poly: poly.distance(coordinates))
                    closest_country = self.map_data.iloc[dist.argmin()].ISO_A2
                    logger.warning(
                        f'Coordinates {longitude}, {latitude} were outside of '
                        'a country land area but were matched to '
                        f'closest country ({closest_country})')
                    return closest_country
            else:
                return None

        def convert_to_polygon(s):
            for i, _s in enumerate(s):
                s[i] = [float(_s[0]), float(_s[1])]
            return shapely.geometry.Polygon(s)

        geo_obj = {
            # 'geo_type': None,
            'longitude': None,
            'latitude': None,
            # 'country_code': None,
            # 'location_type': None
        }

        if self.coordinates:
            # Try to get geo data from coordinates (<0.1% of tweets)
            geo_obj['longitude'], geo_obj['latitude'] = self.coordinates[0:2]
            # For the newer tweets, if there's a coordinates field,
            # there's also a place field
            country_code = self.place.country_code
            if country_code and country_code == '':
                # Sometimes places don't contain country codes,
                # try to resolve from coordinates
                country_code = get_country_code_by_coords(
                    geo_obj['longitude'], geo_obj['latitude'])
            geo_obj['country_code'] = country_code
            geo_obj['location_type'] = self.place.place_type
            geo_obj['geo_type'] = 'tweet.coordinates'
        elif self.place.coordinates:
            # Try to get geo data from place (roughly 1% of tweets)
            # Why does convert_to_polygon take only
            # the first two coordinates? ->
            # It's not the first two coordinates, it's the bounding box,
            # it's for some reason wrapped into another layer of brackets
            # [[[a, b], [c, d], [e, f], [g, h]]]
            polygon = convert_to_polygon(self.place.coordinates[0])
            geo_obj['longitude'] = polygon.centroid.x
            geo_obj['latitude'] = polygon.centroid.y
            country_code = self.place.country_code
            if country_code and country_code == '':
                # Sometimes places don't contain country codes,
                # try to resolve from coordinates
                country_code = get_country_code_by_coords(
                    geo_obj['longitude'], geo_obj['latitude'])
            geo_obj['country_code'] = country_code
            geo_obj['location_type'] = self.place.place_type
            geo_obj['geo_type'] = 'tweet.place'
        else:
            if self.geo_code is None:
                logger.warning(
                    'Not possible to retrieve geo info from '
                    "user location without 'geo_code'")
                return geo_obj
            # Try to parse user location
            locations = self.geo_code.decode(self.user.location)
            # Why len() > 0? -> Because that's the output of self.geo_code
            if len(locations) > 0:
                geo_obj['longitude'] = locations[0]['longitude']
                geo_obj['latitude'] = locations[0]['latitude']
                geo_obj['location_type'] = locations[0]['location_type']
                country_code = locations[0]['country_code']
                if country_code == '':
                    # Sometimes country code is missing (e.g. disputed areas),
                    # try to resolve from geodata
                    country_code = get_country_code_by_coords(
                        geo_obj['longitude'], geo_obj['latitude'])
                geo_obj['country_code'] = country_code
                geo_obj['geo_type'] = 'user.location'

        return geo_obj

    def add_region_info(self, geo_obj):
        """Adds region info to 'geo_obj'.

        Returns:
            geo_obj (dict): A dictionary with added keys:
                - region (str)
                - subregion (str)

        Regions (according to World Bank):
        East Asia & Pacific, Latin America & Caribbean, Europe & Central Asia,
        South Asia, Middle East & North Africa, Sub-Saharan Africa,
        North America, Antarctica.

        Subregions:
        South-Eastern Asia, South America, Western Asia, Southern Asia,
        Eastern Asia, Eastern Africa, Northern Africa Central America,
        Middle Africa, Eastern Europe, Southern Africa, Caribbean,
        Central Asia, Northern Europe, Western Europe, Southern Europe,
        Western Africa, Northern America, Melanesia, Antarctica,
        Australia and New Zealand, Polynesia, Seven seas (open ocean),
        Micronesia.
        """
        def get_region_by_country_code(country_code):
            return self.map_data[
                self.map_data['ISO_A2'] == country_code].iloc[0].REGION_WB \
                if self.map_data else None

        def get_subregion_by_country_code(country_code):
            return self.map_data[
                self.map_data['ISO_A2'] == country_code].iloc[0].SUBREGION \
                if self.map_data else None

        if geo_obj['country_code'] and self.map_data:
            # Retrieve region info
            try:
                geo_obj['region'] = get_region_by_country_code(
                    geo_obj['country_code'])
                geo_obj['subregion'] = get_subregion_by_country_code(
                    geo_obj['country_code'])
            except IndexError:
                # self.map_data[self.map_data['ISO_A2'] == country_code].iloc[0]
                # is invalid
                logger.warning(
                    'Unknown country_code %s', geo_obj['country_code'])

        return geo_obj

    @property
    def media_info(self):
        media_info = {'has_media': False, 'media': {}, 'media_image_urls': []}
        if self.media is None:
            return media_info
        media_info['has_media'] = True
        media_info['media'] = defaultdict(lambda: 0)
        for medium in self.media:
            media_info['media'][medium.get('type')] += 1
            # For media of type video/animated_gif, media_url corresponds to
            # a thumbnail image
            media_info['media_image_urls'].append(medium.get('media_url'))
        media_info['media'] = dict(media_info['media'])
        return media_info

    @property
    def token_count(self):
        text = self.text
        # Remove user handles and URLs from text
        text = anonymize_text(text, '', '', '')
        doc = nlp(text, disable=['parser', 'tagger', 'ner'])
        # Count the number of tokens excluding stopwords
        token_count = len([
            token for token in doc if token.is_alpha and not token.is_stop])
        return token_count

    @property
    def _urls_text(self):
        tweet = self.retweet_or_tweet
        # https://developer.twitter.com/en/docs/twitter-api/v1/enrichments/overview/expanded-and-enhanced-urls
        urls_unwound = [
            url.get('unwound', {}).get('url', '') for url in tweet.urls]
        urls_expanded = [url.get('expanded_url', '') for url in tweet.urls]
        urls_media = []
        if tweet.extended_tweet.media:
            urls_media = [
                medium.get('expanded_url', '')
                for medium in tweet.extended_tweet.media]
        return ' '.join(urls_unwound + urls_expanded + urls_media)

    @property
    def _user_mentions_text(self):
        user_mentions_names = [
            mention['name']
            for mention in self.retweet_or_tweet.user_mentions]
        user_mentions_screen_names = [
            mention['screen_name']
            for mention in self.retweet_or_tweet.user_mentions]
        return ' '.join(user_mentions_names + user_mentions_screen_names)

    @property
    @lru_cache(maxsize=1)
    def keyword_matching_text(self):
        """Returns matching keywords for each project."""
        # Fetch all relevant text
        text = ''
        text += self.text
        text += self._user_mentions_text
        text += self._urls_text
        return text.lower()

    def contains_keywords(self):
        """Emergency function if we need to separate several projects
        mixed in one folder.
        Here we pool all relevant text within the tweet to do the matching.
        From the Twitter docs:
        "Specifically, the text attribute of the Tweet, ``expanded_url`` and
        ``display_url`` for links and media, text for hashtags, and
        ``screen_name`` for user mentions are checked for matches."
        https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html
        """
        if self.keywords == []:
            # None in a boolean column is not good for pandas
            return False

        for keyword in self.keywords:
            if keyword in self.keyword_matching_text:
                return True
        return False
