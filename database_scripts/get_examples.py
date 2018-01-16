import os
import sys
import pickle

import readability

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('white')
sns.set_context('talk')

import tweepy
import HTMLParser
from textblob import TextBlob

import model

consumer_key = 'VLuAoDW7Nq32hUnRBe4IQNBLV'
consumer_secret = '7le9DngZh2JQuarksLwc3weqRfA2jqSos7vK1TqWVOOwr5KpmZ'
access_token = '2358532068-WazrlPbbum4e9S8DbnhVRuYtLNSFLeLFftlIa8A'
access_token_secret = 'CzMF57bRpfzkvxLaFLaR7USRSuHowMrjJq9aw01d7AbJs'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
auth.set_access_token(access_token, access_token_secret) 
twitter_api = tweepy.API(auth)

def twitter(word):
	curs = tweepy.Cursor(twitter_api.search, q=word, lang="en", since="2018-01-01", tweet_mode='extended').items(10000)
	tweet_list = []
	for tweet in curs: tweet_list.append(tweet) 

	text_list = []
	for tweet in tweet_list:
		if (not tweet.retweeted) and ('RT @' not in tweet.full_text) and (tweet.retweet_count>100):			
			text = clean_tweet(tweet)
			words = TextBlob(text)
			text_list.append(words)

	return text_list

#Gets the text, sans links, hashtags, mentions, media, and symbols.
def clean_tweet(tweet):
	# Source: https://gist.github.com/timothyrenner/dd487b9fd8081530509c
	text = tweet.full_text

	html_parser = HTMLParser.HTMLParser()
	text = html_parser.unescape(text)
	text = text.encode("ascii","ignore")

	slices = []
	#Strip out the urls.
	if 'urls' in tweet.entities:
	    for url in tweet.entities['urls']:
	        slices += [{'start': url['indices'][0], 'stop': url['indices'][1]}]

	#Strip out the hashtags.
	if 'hashtags' in tweet.entities:
	    for tag in tweet.entities['hashtags']:
	        slices += [{'start': tag['indices'][0], 'stop': tag['indices'][1]}]

	# #Strip out the user mentions.
	# if 'user_mentions' in tweet.entities:
	#     for men in tweet.entities['user_mentions']:
	#         slices += [{'start': men['indices'][0], 'stop': men['indices'][1]}]

	#Strip out the media.
	if 'media' in tweet.entities:
	    for med in tweet.entities['media']:
	        slices += [{'start': med['indices'][0], 'stop': med['indices'][1]}]

	#Strip out the symbols.
	if 'symbols' in tweet.entities:
	    for sym in tweet.entities['symbols']:
	        slices += [{'start': sym['indices'][0], 'stop': sym['indices'][1]}]

	# Sort the slices from highest start to lowest.
	slices = sorted(slices, key=lambda x: -x['start'])

	#No offsets, since we're sorted from highest to lowest.
	for s in slices:
	    text = text[:s['start']] + text[s['stop']:]
	    
	return text.strip()

def gutenberg(word):
	word_object = model.Word.get_word_object(word)
	passages = word_object.passages
	passages_in_fiction = [passage for passage in passages if passage.parent_doc.doctype == 'book']
	text_list = [TextBlob(passage.get_paragraph()) for passage in passages_in_fiction]

	return text_list

def newspaper(word):
	word_object = model.Word.get_word_object(word)
	passages = word_object.passages
	passages_in_newspaper = [passage for passage in passages if passage.parent_doc.doctype == 'article']
	text_list = [TextBlob(passage.get_paragraph()) for passage in passages_in_newspaper]

	return text_list

def get_polarity(text_blob):
	return text_blob.sentiment.polarity

def get_subjectivity(text_blob):
	return text_blob.sentiment.subjectivity

def get_readability(text_blob):
	return readability.getmeasures(text_blob.words)['readability grades']['FleschReadingEase']

def hist_from_list(sentiment_list):
	plt.hist(sentiment_list)
	plt.show()

if __name__ == '__main__':
	
	word = sys.argv[0]
	twitter_text = twitter(word)
	gutenberg_text = gutenberg(word)
	newspaper_text = newspaper(word)

	out_dict = {}
	out_dict['twitter'] = twitter_text
	out_dict['fiction'] = gutenberg_text
	out_dict['news'] = newspaper_text

	out_text = twitter_text + gutenberg_text + newspaper_text

	polarity_list = [get_polarity(text_blob) for text_blob in out_text]
	subjectivity_list = [get_subjectivity(text_blob) for text_blob in out_text]
	readability_list = [get_readability(text_blob) for text_blob in out_text]