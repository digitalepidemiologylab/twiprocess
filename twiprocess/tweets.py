import logging
import re
import hashlib
from collections import defaultdict

from pandas import to_datetime
import shapely.geometry

from tweet import Tweet
from text import anonymize_text

logger = logging.getLogger(__name__)

try:
    import spacy
except ImportError:
    logger.warning("Could not import 'spacy'. 'get_token_count' won't work.")

nlp = spacy.load('en_core_web_sm')


class ProcessTweet(Tweet):
    """Wrapper class for processing functions."""

    def extract(self):
        geo_obj = self.get_geo_info()
        return {
            'id': self.id,
            'text': self.text,
            'in_reply_to_status_id': self.replied_status_id,
            'in_reply_to_user_id': self.replied_user_id,
            'quoted_user_id': self.quoted_status.user.id,
            'quoted_status_id': self.quoted_status.id,
            'retweeted_user_id': self.retweeted_status.user.id,
            'retweeted_status_id': self.retweeted_status.id,
            'created_at': to_datetime(self.created_at).isoformat(),
            'entities.user_mentions': self.get_user_mentions_ids(),
            'user.id': self.user.id,
            'user.screen_name': self.user.screen_name,
            'user.name': self.user.name,
            'user.description': self.user.description,
            'user.timezone': self.user.time_zone,
            'user.location': self.user.location,
            'user.num_followers': self.user.followers_count,
            'user.num_following': self.user.friends_count,
            'user.created_at': to_datetime(self.user.created_at).isoformat(),
            'user.statuses_count': self.user.statuses_count,
            'user.is_verified': self.user.verified,
            'lang': self.lang,
            'token_count': self.get_token_count(),
            'is_retweet': self.is_retweet,
            'has_quote': self.has_quote,
            'is_reply': self.is_reply,
            'contains_keywords':
                True
                if self._status.get('matching_keywords')
                else self.contains_keywords(),
            **geo_obj
        }

    def get_geo_info(self):
        """
        Tries to infer different types of geoenrichment from tweet
        (PreprocessTweet object).
        Returns:
            geo_obj (dict): A dictionary with the following keys:
                - longitude (float)
                - latitude (float)
                - country_code (str)
                - region (str)
                - subregion (str)
                - geo_type (int)

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
                self.map_data['ISO_A2'] == country_code].iloc[0].REGION_WB

        def get_subregion_by_country_code(country_code):
            return self.map_data[
                self.map_data['ISO_A2'] == country_code].iloc[0].SUBREGION

        def get_country_code_by_coords(longitude, latitude):
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

        def convert_to_polygon(s):
            for i, _s in enumerate(s):
                s[i] = [float(_s[0]), float(_s[1])]
            return shapely.geometry.Polygon(s)

        geo_obj = {
            'longitude': None,
            'latitude': None,
            'country_code': None,
            'region': None,
            'subregion': None,
            'geo_type': 0
        }

        if self.coordinates:
            # Try to get geo data from coordinates (<0.1% of tweets)
            geo_obj['longitude'], geo_obj['latitude'] = self.coordinates[0:2]
            geo_obj['country_code'] = get_country_code_by_coords(
                geo_obj['longitude'], geo_obj['latitude'])
            geo_obj['geo_type'] = 1
        elif self.place_coordinates:
            # Try to get geo data from place (roughly 1% of tweets)
            # Why does convert_to_polygon take only
            # the first two coordinates? ->
            # It's not the first two coordinates, it's the bounding box,
            # it's for some reason wrapped into another layer of brackets
            # [[[a, b], [c, d], [e, f], [g, h]]]
            p = convert_to_polygon(self.place_coordinates[0])
            geo_obj['longitude'] = p.centroid.x
            geo_obj['latitude'] = p.centroid.y
            country_code = self.place_country_code
            if country_code and country_code == '':
                # Sometimes places don't contain country codes,
                # try to resolve from coordinates
                country_code = get_country_code_by_coords(
                    geo_obj['longitude'], geo_obj['latitude'])
            geo_obj['country_code'] = country_code
            geo_obj['geo_type'] = 2
        else:
            # Try to parse user location
            locations = self.geo_code.decode(self.user.location)
            # Why len() > 0? -> Because that's the output of self.geo_code
            if len(locations) > 0:
                geo_obj['longitude'] = locations[0]['longitude']
                geo_obj['latitude'] = locations[0]['latitude']
                country_code = locations[0]['country_code']
                if country_code == '':
                    # Sometimes country code is missing (e.g. disputed areas),
                    # try to resolve from geodata
                    country_code = get_country_code_by_coords(
                        geo_obj['longitude'], geo_obj['latitude'])
                geo_obj['country_code'] = country_code
                geo_obj['geo_type'] = 3

        if geo_obj['country_code']:
            # Retrieve region info
            if geo_obj['country_code'] in self.map_data.ISO_A2.tolist():
                geo_obj['region'] = get_region_by_country_code(
                    geo_obj['country_code'])
                geo_obj['subregion'] = get_subregion_by_country_code(
                    geo_obj['country_code'])
            else:
                logger.warning(
                    f'Unknown country_code {geo_obj["country_code"]}')
        return geo_obj

    def get_user_mentions_ids(self):
        # TODO: Parse user mentions in case of no mentions on Twitter's side?
        # TODO: Originally, doesn't handle retweets
        # Edited invalid status['extended_tweet']['entities']['user_mentions']
        # to status['entities']['user_mentions']
        user_mentions = [
            mention['id_str']
            for mention in self.retweet_or_tweet.user_mentions]
        if user_mentions == []:
            return None
        return user_mentions

    def get_media_info(self, tweet_obj=None):
        # TODO: Whatfor?
        if tweet_obj is None:
            tweet_obj = self.tweet
        media_info = {'has_media': False, 'media': {}, 'media_image_urls': []}
        if self._keys_exist(tweet_obj, 'extended_tweet', 'extended_entities', 'media'):
            tweet_media = tweet_obj['extended_tweet']['extended_entities']['media']
        elif self._keys_exist(tweet_obj, 'extended_entities', 'media'):
            tweet_media = tweet_obj['extended_entities']['media']
        else:
            return media_info
        media_info['has_media'] = True
        media_info['media'] = defaultdict(lambda: 0)
        for m in tweet_media:
            media_info['media'][m['type']] += 1
            # for media of type video/animated_gif media_url corresponds to a thumbnail image
            media_info['media_image_urls'].append(m['media_url'])
        media_info['media'] = dict(media_info['media'])
        return media_info

    def contains_keywords(self):
        """Here we pool all relevant text within the tweet to do the matching.
        From the Twitter docs:
        "Specifically, the text attribute of the Tweet, ``expanded_url`` and
        ``display_url`` for links and media, text for hashtags, and
        ``screen_name`` for user mentions are checked for matches."
        https://developer.twitter.com/en/docs/tweets/filter-realtime/guides/basic-stream-parameters.html
        """
        # TODO: We're not fetching display_url, should we?
        if self.keywords == []:
            # TODO: Ask Martin
            return None  # Was False

        relevant_text = ''
        relevant_text += self.text
        relevant_text += self._get_user_mentions_text()
        relevant_text = relevant_text.lower()

        relevant_urls = ''
        relevant_urls += self._get_urls_text()
        relevant_urls = relevant_urls.lower()

        for keyword in self.keywords:
            # Anything inside the text (mentions, hashtags) will be matched
            match = re.search(r'{}'.format(keyword), relevant_text)
            if match is not None:
                return True
            # Match URLs if surrounded by non-alphabetic characters
            # TODO: Is it somehow important?
            match = re.search(
                r'(\b|\d|_){}(\b|\d|_|cas)'.format(keyword), relevant_urls)
            if match is not None:
                return True
        return False

    def get_token_count(self):
        text = self.text
        # Remove user handles and URLs from text
        text = anonymize_text(text, '', '', '')
        doc = nlp(text, disable=['parser', 'tagger', 'ner'])
        # Count the number of tokens excluding stopwords
        token_count = len([
            token for token in doc if token.is_alpha and not token.is_stop])
        return token_count

    def get_text_hash(self):
        # TODO: Whatfor?
        return hashlib.md5(self.text.encode('utf-8')).hexdigest()

    # Private methods

    def _get_urls_text(self):
        tweet = self.retweet_or_tweet
        # https://developer.twitter.com/en/docs/twitter-api/v1/enrichments/overview/expanded-and-enhanced-urls
        urls_unwound = [
            url.get('unwound', {}).get('url', '') for url in tweet.urls]
        urls_expanded = [url.get('expanded_url', '') for url in tweet.urls]
        urls_media = [
            medium.get('expanded_url', '')
            for medium in tweet.extended_tweet.media]
        return ' '.join(urls_unwound + urls_expanded + urls_media)

    def _get_user_mentions_text(self):
        user_mentions_names = [
            mention['name']
            for mention in self.retweet_or_tweet.user_mentions]
        user_mentions_screen_names = [
            mention['screen_name']
            for mention in self.retweet_or_tweet.user_mentions]
        return ' '.join(user_mentions_names + user_mentions_screen_names)
