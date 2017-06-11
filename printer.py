import local_secrets
import tweepy
import dataset
from sqlalchemy.exc import ProgrammingError
import json

auth = tweepy.OAuthHandler(local_secrets.TWITTER_APP_KEY, local_secrets.TWITTER_APP_SECRET)

auth.set_access_token(local_secrets.TWITTER_KEY, local_secrets.TWITTER_SECRET)

api = tweepy.API(auth)

class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        if status.geo is not None:
        	if status.geo['coordinates'] is not None:
	    	    print(status)
        return True
    def on_error(self, status_code):
        if status_code == 420:
            return False

stream_listener = StreamListener()
stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
stream.filter(locations=[-180,-90,180,90])


