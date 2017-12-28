#!/usr/bin/env python

import requests
from textblob import TextBlob
from twitter import Twitter
import time
import ccxt
from coins import coins
from notifier import Notifier

symbol_name = {}
name_symbol = {}
symbol_exchange = {}
bot = None
notifier = Notifier()

def get_coins_bittrex():
    exchange = ccxt.bittrex()
    markets = exchange.fetch_markets()
    try:
        for market in markets:
            market = market['info']
            symbol = market["MarketCurrency"]
            name = market["MarketCurrencyLong"].lower()
            symbol_name[symbol] = name
            name_symbol[name] = symbol
            symbol_exchange[symbol] = 'bittrex'
        # print(f'Found {len(markets)} markets.')
    except Exception as e:
        print(f'Failed to get markets from Bittrex ({e})')

def get_coins_liqui():
    exchange = ccxt.liqui()
    markets = exchange.fetch_markets()
    try:
        for market in markets:
            symbol = market['base']
            try:
                name = coins[symbol].lower()
            except Exception as e:
                # print(f'Failed to match ' + symbol + '. Consider adding to coins.py.')
                continue
            symbol_name[symbol] = name
            name_symbol[name] = symbol
            symbol_exchange[symbol] = 'liqui'
        # print(f'Found {len(markets)} markets.')
    except Exception as e:
        print(f'Failed to get markets from Liqui ({e})')

def extract_symbols(text):
    """Return trading symbols of cryptocurrencies in text in format (symbol, name) e.g. ("BTC", "bitcoin")"""
    symbols = set()
    ignore_tags = ["DT"]
    words = [w[0].lower() for w in TextBlob(text).tags if w[1] not in ignore_tags]
    for word in words:
        if word.upper() in symbol_name:
            symbols.add((word.upper(), symbol_name[word.upper()]))
            # print(f'Found symbol: {word.upper()}')
        elif word.lower() in name_symbol:
            symbols.add((name_symbol[word.lower()], word.lower()))
            # print(f'Found symbol: {name_symbol[word]}')

    return symbols

def get_sentiment_analysis(text, coins):
    """Return the sentiment analysis of coins mentioned in text in
    the form of a dictionary that aggregates the sentiment of
    sentences that include each of the coins.
    """
    sentiment = {}
    blob = TextBlob(text)
    for sentence in blob.sentences:
        lowercase_words = [x.lower() for x in sentence.words]
        for coin in coins:
            if coin[0].lower() in lowercase_words or coin[1].lower() in lowercase_words:
                try:
                    sentiment[coin] += sentence.sentiment.polarity
                except:
                    sentiment[coin] = sentence.sentiment.polarity

    return sentiment, blob.sentiment.polarity


def get_verdict(sentiment, overall):
    """Use the result from get_sentiment_analysis to determine which coins to buy and
    return an array of coin symbols e.g. ["XVG", "DGB"]"""
    to_buy = [x for x in sentiment.keys() if sentiment[x] >= 0]
    if overall >= 0:
        # Filter out large coins (ideally take out coins in top 10)
        to_buy = [x for x in to_buy if x[0] not in ["BTC", "LTC", "ETH"]]
        return to_buy
    else:
        return []


def analyze(text):
    """
    1. Extract symbols
    2. Get sentiment analysis
    3. Determine which coins to buy
    """
    coins = extract_symbols(text)
    if coins:
        sentiment, overall = get_sentiment_analysis(text, coins)
        to_buy = get_verdict(sentiment, overall)

        return to_buy
    return []


def filter_coins(to_buy):
    f = ['OK', 'PAY', 'BLOCK', 'RISE', 'TIME']
    filtered = [x for x in to_buy if x[0] not in f]
    return filtered


def twitter_tweet_callback(text, user, link):
    to_buy = analyze(text)
    to_buy = filter_coins(to_buy)
    if len(to_buy) > 0:
        msg = str(to_buy) + ".\nTweet: " + text + ".\n" + link
        # print(msg)
        notifier.buy(msg)

if __name__ == "__main__":
    # Populate coins. Ordering determines exchange at which to buy.
    # Lowest to highest priority (e.g. last call is most prioritized exchange).
    get_coins_bittrex()
    get_coins_liqui()

    #print(symbol_name)
    #print(name_symbol)

    # Twitter stream
    twitter = Twitter(setup=['stream'], tweet_callback=twitter_tweet_callback)
