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

## only verified accounts for twitter ##
## blogs ##
## reader level ##

def twitter(word):
    curs = tweepy.Cursor(twitter_api.search, q=word, lang="en", since="2018-01-01", tweet_mode='extended').items(1000)
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

def get_metric_lists(text_list):
    polarity_list = [get_polarity(text_blob) for text_blob in text_list]
    subjectivity_list = [get_subjectivity(text_blob) for text_blob in text_list]
    readability_list = [get_readability(text_blob) for text_blob in text_list]
    return [polarity_list, subjectivity_list, readability_list]

def doc2vec(text_list):
    from gensim.models.doc2vec import LabeledSentence
    for index, text in enumerate(text_list):                                                                                        
        documents.append(LabeledSentence(words=text.words, tags=[u'SENT_'+str(index)]))  
    model = Doc2Vec(documents, size=100, window=8, min_count=5, workers=4)
    return model, documents

def get_similarity_matrix(model, documents)
    out_df = pd.DataFrame(index=range(len(documents)), columns=range(len(documents)))

    for index, document in enumerate(documents):
        temp_series = pd.Series(index=range(len(documents)), name=index)
        tokens = document.words
        new_vector = model.infer_vector(tokens)
        sims = model.docvecs.most_similar([new_vector], topn=len(documents))
        temp_df = pd.DataFrame(sims)
        indices = pd.DataFrame(temp_df[0].str.split('_').tolist(), columns=['SENT', 'Indices'])['Indices'].astype(int).tolist()
        out_df[index] = pd.Series(temp_df[1].values, index=indices, name=index)

    return out_df

def tf_idf(text_list):
    from sklearn.feature_extraction.text import TfidfVectorizer
    model = TfidfVectorizer()
    result = model.fit_transform([str(text) for text in text_list])
    return result

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