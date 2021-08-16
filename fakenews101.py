import config
import requests
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import imp
import sys
sys.modules["sqlite"] = imp.new_module("sqlite")
sys.modules["sqlite3.dbapi2"] = imp.new_module("sqlite.dbapi2")
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv
import pandas as pd

sia = SentimentIntensityAnalyzer()
# Loughran and McDonald
positive = []
with open('lm_positive.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        positive.append(row[0].strip())
    
negative = []
with open('lm_negative.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        entry = row[0].strip().split(" ")
        if len(entry) > 1:
            negative.extend(entry)
        else:
            negative.append(entry[0])

final_lex = {}
final_lex.update({word:2.0 for word in positive})
final_lex.update({word:-2.0 for word in negative})
final_lex.update(sia.lexicon)
sia.lexicon = final_lex
 
# The main URL for the Telegram API with our bot's token
BASE_URL = "https://api.telegram.org/bot{}".format(config.bot_token)

def is_url(url):
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False

def receive_message(update):
    """Receive a raw message from Telegram"""
    try:
        chat_id = update["message"]["chat"]["id"]
        chat_name = update["message"]["chat"]["first_name"]
        message = update["message"]["text"]
        return chat_id, chat_name, message
    except Exception as e:
        print(e)
        return (None, None)
 
def handle_message(chat_id, chat_name, message):
    """Calculate a response to the message"""
    if message == "/start":
        send_message(chat_id, "Welcome {}. Send me your article's URL and I will help you determine the sentiment of the content.".format(chat_name))

    elif message == "/about":
        send_message(chat_id, "This bot currently uses a trained sentiment analysis model to determine the sentiment of the content from a given URL.\nIt does so using 5 heuristics to analyse the sentiment.\n1. Punctuation\n2. Capitalization\n3. Degree modifiers\n4. Conjunctions\n5. Preceding Tri-gram")

    elif is_url(message):
        url = message
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
        req = Request(url=url, headers=headers) 
        try:
            link_page = urlopen(req).read()
        except:
            url = url[:-2]
            req = Request(url=url, headers=headers) 
            link_page = urlopen(req).read()
        link_soup = BeautifulSoup(link_page)
        sentences = link_soup.findAll("p")
        passage = ""
        for sentence in sentences:
            passage += sentence.text
        sentiment = sia.polarity_scores(passage)['compound']
        if sentiment == 0.0:
            send_message(chat_id, "There doesn't seem to be any content for me to analyse in this URL, please try again.")

        elif -0.3 <= sentiment < 0.3:
            send_message(chat_id, "The content of this URL seems to be generally quite neutral. On a scale of -1 to 1, I give it a {}.".format(sentiment))

        elif -0.6 <= sentiment < -0.3:
            send_message(chat_id, "The content of this URL seems to be generally quite negative. On a scale of -1 to 1, I give it a {}.".format(sentiment))

        elif 0.3 <= sentiment < 0.6:
            send_message(chat_id, "The content of this URL seems to be generally quite positive. On a scale of -1 to 1, I give it a {}.".format(sentiment))

        elif -1.0 <= sentiment < -0.6:
            send_message(chat_id, "The content of this URL seems to be quite negative. On a scale of -1 to 1, I give it a {}.".format(sentiment))

        elif 0.6 <= sentiment <= 1.0:
            send_message(chat_id, "The content of this URL seems to be quite positive. On a scale of -1 to 1, I give it a {}.".format(sentiment))
        
    else:
        send_message(chat_id, "Invalid URL, please try again.")
 
def send_message(chat_id, message):
    """Send a message to the Telegram chat defined by chat_id"""
    url = BASE_URL + "/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    r = requests.post(url, json=payload)
    return r
        
def main(update):
    """Receive a message, handle it, and send a response"""
    try:
        chat_id, chat_name, message = receive_message(update)
        handle_message(chat_id, chat_name, message)
    except Exception as e:
        print(e)

