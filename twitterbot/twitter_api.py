import logging
import os

from dotenv import load_dotenv, find_dotenv
import tweepy

load_dotenv(find_dotenv())
consumer_token = os.environ.get('API_KEY')
consumer_secret = os.environ.get('API_SECRET_KEY')
access_token = os.environ.get('ACCESS_TOKEN')
access_token_secret = os.environ.get('ACCESS_SECRET')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def connect_to_api(consumer_token=consumer_token,
                   consumer_secret=consumer_secret,
                   access_token=access_token,
                   access_token_secret=access_token_secret):

    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    try:
        api = tweepy.API(auth)
    except Exception as e:
        logger.error(f'Error connecting to API: {e}')
        raise e
    return api


def get_followings(username):
    api = connect_to_api()
    friends = []
    for friend in tweepy.Cursor(api.friends).items():
        friends.append(friend)
    return api.friends_ids(), friends


if __name__ == '__main__':
    username = os.environ.get('MY_USER_NAME')
    ids, friends = get_followings(username)
