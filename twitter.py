import io
from PIL import Image
import pytesseract
import requests
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
from tweepy import Cursor
from tweepy import API


with open("config.json") as f:
    config = json.load(f)
    FOLLOW_IDS = config["TWITTER_FOLLOW_IDS"]
    CONSUMER_KEY = config["TWITTER_CONSUMER_KEY"]
    CONSUMER_SECRET = config["TWITTER_CONSUMER_SECRET"]
    ACCESS_KEY = config["TWITTER_ACCESS_KEY"]
    ACCESS_SECRET = config["TWITTER_ACCESS_SECRET"]


class TwitterListener(StreamListener):

    def __init__(self, callback):
        self.callback = callback

    def on_data(self, data):
        tweet_json = json.loads(data)
        try:
            if tweet_json["user"]["id_str"] in FOLLOW_IDS:
                print(tweet_json["text"])
                self.callback(tweet_json)
        except:
            pass

class CursorListener:
    def __init__(self, auth, callback):
        self.auth = auth
        self.callback = callback
        self.api = API(self.auth)

    def run(self):
        for uid in FOLLOW_IDS:
            cursor = Cursor(self.api.user_timeline, user_id=uid)
            for status in cursor.items(100):
                # print(status._json)
                self.callback(status._json)


class Twitter:
    def __init__(self, setup=['stream'], tweet_callback=lambda x, y, z: x, image_only=False):
        self.tweet_callback = tweet_callback
        self.image_only = image_only

        self.listener = TwitterListener(self.handle_tweet)

        self.auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

        if 'stream' in setup:
            print('Starting to listen to twitter stream...')
            self.stream = None
            self.run_stream()

        if 'cursor' in setup:
            print('Starting to scan twitter timeline...')
            self.cursor = CursorListener(self.auth, self.handle_tweet)
            self.cursor.run()

    def run_stream(self):
        while True:
            self.stream = Stream(self.auth, self.listener, timeout=60)
            self.stream.filter(follow=FOLLOW_IDS)
            try:
                self.stream.userstream()
            except Exception as e:
                print("Error. Restarting Stream.... Error: ")
                print(e.__doc__)
                print(e.message)

    def handle_tweet(self, tweet_json):
        screen_name = tweet_json["user"]["screen_name"]
        id = tweet_json["id_str"]
        text = tweet_json["text"].replace("\\", "")
        is_image = False
        # Get media if present
        try:
            urls = [x["media_url"].replace("\\", "") for x in tweet_json["entities"]["media"] if x["type"] == "photo"]
            for url in urls:
                response = requests.get(url)
                img = Image.open(io.BytesIO(response.content))
                # Extract text from image
                # print(img)
                is_image = True
                img_text = pytesseract.image_to_string(img)
                text += f' . {img_text}'
        except KeyError:
            pass

        link = f'https://twitter.com/{screen_name}/status/{id}'

        try:
            if not self.image_only or (self.image_only and is_image):
                self.tweet_callback(text, screen_name, link)
        except:
            pass

if __name__ == "__main__":
    import time
    twitter = Twitter()
    print('Twitter done.')
    while True:
        time.sleep(1)
