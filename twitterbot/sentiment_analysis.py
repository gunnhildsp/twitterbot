import re
from textblob import TextBlob


def clean_text(text):
    return " ".join(
        re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text).split()
    )


def text_sentiment(text):
    text = clean_text(text)
    blob = TextBlob(text)

    return blob.sentiment
