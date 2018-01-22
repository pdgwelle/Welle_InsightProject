import os
import sys
import pickle
import random

import numpy as np

import readability

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('white')
sns.set_context('talk')

import tweepy
import HTMLParser
from textblob import TextBlob

import model
import secrets

auth = tweepy.OAuthHandler(secrets.consumer_key, secrets.consumer_secret) 
auth.set_access_token(secrets.access_token, secrets.access_token_secret) 
twitter_api = tweepy.API(auth)

def twitter(word):
    curs = tweepy.Cursor(twitter_api.search, q=word, lang="en", since="2018-01-01", tweet_mode='extended').items(100)
    tweet_list = []
    for tweet in curs: tweet_list.append(tweet) 

    text_list = []
    for tweet in tweet_list:
        if (not tweet.retweeted) and ('RT @' not in tweet.full_text):         
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

def get_metric_lists(text_list):
    polarity_list = [get_polarity(text_blob) for text_blob in text_list]
    subjectivity_list = [get_subjectivity(text_blob) for text_blob in text_list]
    readability_list = [get_readability(text_blob) for text_blob in text_list]
    return [polarity_list, subjectivity_list, readability_list]

def tf_idf(text_list):
    from sklearn.feature_extraction.text import TfidfVectorizer
    model = TfidfVectorizer()
    result = model.fit_transform([str(text) for text in text_list])
    return result

def retrieve_examples(word, source, ranks):

    def modify_normalized_distribution(normalized_array, rank):
        if(rank == 1): return normalized_array
        elif(rank == -1): return -1 * normalized_array
        elif(rank == 0):
            array = -1 * np.abs(normalized_array)
            renormalized_array = (array - np.mean(array)) / np.std(array)
            return renormalized_array

    def rank_posts(metric_lists, ranks):
        np_polarity = np.array(metric_lists[0])
        np_subj = np.array(metric_lists[1])
        np_read = np.array(metric_lists[2])

        normalized_polarity = (np_polarity - np.mean(np_polarity)) / np.std(np_polarity)
        normalized_subj = (np_subj - np.mean(np_subj)) / np.std(np_subj)
        normalized_read = (np_read - np.mean(np_read)) / np.std(np_read)

        modified_normalized_polarity = modify_normalized_distribution(normalized_polarity, ranks[0])
        modified_normalized_subj = modify_normalized_distribution(normalized_subj, ranks[1])
        modified_normalized_read = modify_normalized_distribution(normalized_read, ranks[2])

        cumulative_score = modified_normalized_polarity + modified_normalized_subj + modified_normalized_read
        return cumulative_score

    def get_upper_half_text(text, ranked_scores):
        text = np.array(text)
        ranked_scores = np.array(ranked_scores)
        out_text = text[ranked_scores > np.median(ranked_scores)]
        return out_text

    def shorten_text(text_list, word):
        out_list = []
        for text in text_list:
            if(len(text) > 750):
                sentence_index = np.where([word in array for array in np.array(text.lower().split('.'))])[0][0]
                out_text = text.split('.')[sentence_index] + '.'
                offset_list = [-1,1,-2,2,-3,3,-4,4,-5,5]
                for offset in offset_list:
                    if(len(out_text) > 100): break
                    index = sentence_index + offset
                    if(index < 0): continue
                    if(offset < 0):
                        out_text = text.split('.')[index] + '.' + out_text
                    elif(offset > 0):
                        out_text = out_text + text.split('.')[index] + '.'
                out_text = out_text.strip()
                out_list.append(out_text)
            else:
                out_list.append(text)
        return out_list

    if(source == 'fiction'):
        text = gutenberg(word)
    elif(source == 'news'):
        text = newspaper(word)
    elif(source == 'twitter'):
        text = twitter(word)

    metric_lists = get_metric_lists(text)
    ranked_scores = rank_posts(metric_lists, ranks)
    upper_half_text = get_upper_half_text(text, ranked_scores)

    text_list = random.sample(text, 3)
    text_list = shorten_text(text_list, word)
    text_list = [unicode(text) for text in text_list]

    return text_list

if __name__ == '__main__':
    
    word = sys.argv[0]
    twitter_text = twitter(word)
    gutenberg_text = gutenberg(word)
    newspaper_text = newspaper(word)

    out_dict = {}
    out_dict['twitter'] = [twitter_text] + get_metric_lists(twitter_text)
    out_dict['fiction'] = [gutenberg_text] + get_metric_lists(gutenberg_text)
    out_dict['news'] = [newspaper_text] + get_metric_lists(newspaper_text)

    out_text = twitter_text + gutenberg_text + newspaper_text

    polarity_list = [get_polarity(text_blob) for text_blob in out_text]
    subjectivity_list = [get_subjectivity(text_blob) for text_blob in out_text]
    readability_list = [get_readability(text_blob) for text_blob in out_text]