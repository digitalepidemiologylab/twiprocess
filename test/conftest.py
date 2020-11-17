import pytest
import json

from twiprocess.processtweet import ProcessTweet


@pytest.fixture(scope='function')
def process_tweet():
    with open('tweet.json', 'r') as f:
        status = json.load(f)
    return ProcessTweet(status)
