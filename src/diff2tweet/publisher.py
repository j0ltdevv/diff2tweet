from __future__ import annotations
import os
import tweepy

def post_to_x(text: str) -> str:
    auth = tweepy.OAuth1UserHandler(
        os.environ['X_API_KEY'],
        os.environ['X_API_SECRET'],
        os.environ['X_ACCESS_TOKEN'],
        os.environ['X_ACCESS_SECRET'],
    )
    client = tweepy.Client(
        consumer_key=os.environ['X_API_KEY'],
        consumer_secret=os.environ['X_API_SECRET'],
        access_token=os.environ['X_ACCESS_TOKEN'],
        access_token_secret=os.environ['X_ACCESS_SECRET'],
    )
    resp = client.create_tweet(text=text)
    return str(resp.data['id'])
