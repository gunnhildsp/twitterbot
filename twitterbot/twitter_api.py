import datetime
import logging
from operator import attrgetter
import os
import time

from dotenv import load_dotenv, find_dotenv
import numpy as np
import pandas as pd
import tweepy

from twitterbot.sentiment_analysis import text_sentiment

load_dotenv(find_dotenv())
consumer_token = os.environ.get("API_KEY")
consumer_secret = os.environ.get("API_SECRET_KEY")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_SECRET")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def connect_to_api(
    consumer_token=consumer_token,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
):

    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    try:
        api = tweepy.API(auth)
    except Exception as e:
        logger.error(f"Error connecting to API: {e}")
        raise e
    return api


def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15 * 60)


def get_followings(api):
    friends = []
    for friend in limit_handled(tweepy.Cursor(api.friends).items()):
        friends.append(friend)
    return api.friends_ids(), friends


def get_recent_tweets(api, user_id, time_start, return_tweets, num_tweets=50):
    """

    :param api: tweepy.API object to connect
    :param user_id: User to get tweets from
    :param time_start: Oldest time to get tweets for
    :param return_tweets: Number of tweets to return
    :param num_tweets: Maximum number of tweets to fetch from api
    :return: list of tweepy.Status objects
    """

    tweets = api.user_timeline(
        user_id, count=max(2 * num_tweets, 10), tweet_mode="extended"
    )
    tweets.sort(key=attrgetter("created_at"), reverse=True)
    oldest_date = tweets[-1].created_at
    # Only return tweets that are newer than start_time and not comments
    tweets = [
        t
        for t in tweets
        if t.created_at > time_start and t.in_reply_to_status_id is None
    ]
    # If desired number of tweets is found or not enough tweets newer than time_start
    if (
        len(tweets) >= return_tweets or oldest_date <= time_start
    ):  # check age of oldest tweets
        # find out how many tweets to return
        length_to_return = min(len(tweets), return_tweets)
        return tweets[0:length_to_return]
    else:
        # If not enough tweets returned and more tweets are available,
        # Call function again but get more tweets from api
        num_tweets = 2 * num_tweets
        return get_recent_tweets(api, user_id, time_start, return_tweets, num_tweets)


def format_tweets(tweets):
    if not tweets:
        return None
    else:
        cols = [
            "created_at",
            "text",
            "user_id",
            "user_screen_name",
            "favorite_count",
            "retweet_count",
        ]
        tweet_df = pd.DataFrame(columns=cols)
        df_tmp_list = []
        for tweet in tweets:
            try:
                text = tweet.text
            except AttributeError:
                text = tweet.full_text
            df_tmp = pd.DataFrame(
                data=[
                    [
                        tweet.created_at,
                        text,
                        tweet.user.id,
                        tweet.user.screen_name,
                        tweet.favorite_count,
                        tweet.retweet_count,
                    ]
                ],
                columns=cols,
            )
            df_tmp_list.append(df_tmp)
        tweet_df = tweet_df.append(df_tmp_list, sort=False)
    return tweet_df


def unfollow_users_with_old_posts(maximum_age_days):
    api = connect_to_api()
    user_ids, friends = get_followings(api)
    time = datetime.datetime.now() - datetime.timedelta(days=maximum_age_days)
    for user_id in user_ids:
        tweet = get_recent_tweets(api, user_id, time, 1)
        if not tweet:
            logger.info(
                f"Unfollowing user_id {user_id} as there are no tweets on their timeline"
            )
            api.destroy_friendship(user_id)
        else:
            duration = datetime.datetime.now() - tweet.created_at
            if duration.days > maximum_age_days:
                logger.info(
                    f'Unfollowing user "{tweet.user.name}" as the newest post is {duration.days} days old'
                )
                api.destroy_friendship(user_id)


def analyse_tweets(tweet_df):
    tweet_df["subjectivity"] = np.nan
    tweet_df["polarity"] = np.nan
    for row in tweet_df.itertuples():
        sentiment_tuple = text_sentiment(row.text)
        tweet_df.loc[row.Index, "polarity"] = sentiment_tuple.polarity
        tweet_df.loc[row.Index, "subjectivity"] = sentiment_tuple.subjectivity
    return tweet_df


def get_tweets_with_sentiments(no_of_days, api):
    oldest_date = datetime.datetime.now() - datetime.timedelta(days=no_of_days)
    user_ids, _ = get_followings(api)
    list_of_df = []
    for user_id in user_ids:
        tweets = get_recent_tweets(api, user_id, oldest_date, return_tweets=20)
        tweet_df = format_tweets(tweets)
        list_of_df.append(tweet_df)
    tweet_df = pd.concat(list_of_df, ignore_index=True)
    tweet_df = analyse_tweets(tweet_df)
    return tweet_df


if __name__ == "__main__":
    # Clean friends list
    # tweet_age_days = 365
    # unfollow_users_with_old_posts(tweet_age_days)

    # Get tweets during recent week
    # TODO add visualisation library that can plot distributions and checks
    # Maybe create notebook with plots
    no_of_days = 7
    api = connect_to_api()
    tweet_df = get_tweets_with_sentiments(no_of_days, api)
    print(tweet_df.text)
