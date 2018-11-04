from twitterbot.sentiment_analysis import clean_text, text_sentiment


def test_clean_text():
    test_text = r"RT @some_user_screen_name https:\\t.co/1234"
    illegal_chars = ["@", "\\", ":", r".", "_"]
    test_text_cleaned = clean_text(test_text)
    assert all([r not in test_text_cleaned for r in illegal_chars])


def test_text_sentiment():
    test_text = "This is a very happy and amazing text example"
    sentiment = text_sentiment(test_text)
    assert isinstance(sentiment.polarity, float)
    assert isinstance(sentiment.subjectivity, float)
