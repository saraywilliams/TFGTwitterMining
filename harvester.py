import local_secrets
import tweepy
import dataset
from sqlalchemy.exc import ProgrammingError
import json

auth = tweepy.OAuthHandler(local_secrets.TWITTER_APP_KEY, local_secrets.TWITTER_APP_SECRET)

auth.set_access_token(local_secrets.TWITTER_KEY, local_secrets.TWITTER_SECRET)

api = tweepy.API(auth)

db = dataset.connect(local_secrets.CONNECTION_STRING)

class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        description = status.user.description
        loc = status.user.location
        text = status.text
        coords = status.coordinates
        coords_lat = None
        coords_lon = None
        geo = status.geo
        geo_lat = None
        geo_lon = None
        name = status.user.screen_name
        user_created = status.user.created_at
        followers = status.user.followers_count
        id_str = status.id_str
        created = status.created_at
        retweets = status.retweet_count
        if geo is not None:
            if geo['coordinates'] is not None:
                geo_lat = geo['coordinates'][0]
                geo_lon = geo['coordinates'][1]
            geo = json.dumps(geo)            
        if coords is not None:
            if coords['coordinates'] is not None:
                    coords_lat = coords['coordinates'][1]
                    coords_lon = coords['coordinates'][0]
            coords = json.dumps(coords)
        table = db[local_secrets.TABLE_NAME]
        try:
            table.insert(dict(
                user_description=description,
                user_location=loc,
                coordinates=coords,
                coordinaes_lat=coords_lat,
                coordinates_lon=coords_lon,
                text=text,
                geo=geo,
                geo_lat=geo_lat,
                geo_lon=geo_lon,
                user_name=name,
                user_created=user_created,
                user_followers=followers,
                id_str=id_str,
                created=created,
                retweet_count=retweets,
            ))
        except ProgrammingError as err:
            print(err)
        return True
    def on_error(self, status_code):
        if status_code == 420:
            return False
        
    def _run(self):
        # Authenticate
        url = "https://%s%s" % (self.host, self.url)

        # Connect and process the stream
        error_counter = 0
        resp = None
        exc_info = None
        while self.running:
            if self.retry_count is not None:
                if error_counter > self.retry_count:
                    # quit if error count greater than retry count
                    break
            try:
                auth = self.auth.apply_auth()
                resp = self.session.request('POST',
                                            url,
                                            data=self.body,
                                            timeout=self.timeout,
                                            stream=True,
                                            auth=auth,
                                            verify=self.verify)
                if resp.status_code != 200:
                    if self.listener.on_error(resp.status_code) is False:
                        break
                    error_counter += 1
                    if resp.status_code == 420:
                        self.retry_time = max(self.retry_420_start,
                                              self.retry_time)
                    sleep(self.retry_time)
                    self.retry_time = min(self.retry_time * 2,
                                          self.retry_time_cap)
                else:
                    error_counter = 0
                    self.retry_time = self.retry_time_start
                    self.snooze_time = self.snooze_time_step
                    self.listener.on_connect()
                    if resp is not None:
                        self._read_loop(resp)
            except (Timeout, ssl.SSLError) as exc:
                # This is still necessary, as a SSLError can actually be
                # thrown when using Requests
                # If it's not time out treat it like any other exception
                if isinstance(exc, ssl.SSLError):
                    if not (exc.args and 'timed out' in str(exc.args[0])):
                        exc_info = sys.exc_info()
                        break
                if self.listener.on_timeout() is False:
                    break
                if self.running is False:
                    break
                sleep(self.snooze_time)
                self.snooze_time = min(self.snooze_time + self.snooze_time_step,
                                       self.snooze_time_cap)
            except Exception as exc:
                exc_info = sys.exc_info()
                # any other exception is fatal, so kill loop
                break

        # cleanup
        self.running = False
        if resp:
            resp.close()

        self.new_session()

        if exc_info:
            # call a handler first so that the exception can be logged.
            self.listener.on_exception(exc_info[1])
            six.reraise(*exc_info)    

while True:
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener, timeout=60)
    stream.filter(locations=[2.052498,41.320881,2.228356,41.461511])
    
    try:
        stream.userstream()

    except Exception as e:
        print("Error. Restarting Stream.... Error: ")


