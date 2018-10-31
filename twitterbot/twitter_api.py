from datetime import datetime
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


def get_followings(api):
    friends = []
    for friend in tweepy.Cursor(api.friends).items():
        friends.append(friend)
    return api.friends_ids(), friends


def get_most_recent_status(api, user_id):
    # Trying to handle pinned tweets and commenting by fetching five tweets and returning the newest

    tweets = api.user_timeline(user_id, count=5)
    if not tweets:
        logger.info(f'No tweets for user_id {user_id}')
        return None

    # Removing tweets that are replies to others (=comments)
    tweets = [t for t in tweets if t.in_reply_to_status_id is None]
    if not tweets:
        logger.info(f'Could not find any tweets that were not comments for user_id {user_id}')
        return None

    # Find newest of remaining
    newest_tweet = tweets[0]
    for tweet in tweets[1:]:
        if tweet.created_at > newest_tweet.created_at:
            newest_tweet = tweet

    return newest_tweet


def unfollow_users_with_old_posts(maximum_age_days):
    api = connect_to_api()
    user_ids, friends = get_followings(api)
    for user_id in user_ids:
        tweet = get_most_recent_status(api, user_id)
        if not tweet:
            logger.info(f'Unfollowing user_id {user_id} as there are no tweets on their timeline')
            api.destroy_friendship(user_id)
        else:
            tweet_time = tweet.created_at
            duration = datetime.now() - tweet_time
            if duration.days > maximum_age_days:
                logger.info(f'Unfollowing user "{tweet.user.name}" as the newest post is {duration.days} days old')
                api.destroy_friendship(user_id)


if __name__ == '__main__':
    unfollow_users_with_old_posts(365)

    api = connect_to_api()
    user_ids, _ = get_followings(api)
    for user_id in user_ids:
        tweet = get_most_recent_status(api, user_id)
        if tweet:
            logger.debug(f'Tweeted by {tweet.user.screen_name} at {tweet.created_at}: \n {tweet.text}')
