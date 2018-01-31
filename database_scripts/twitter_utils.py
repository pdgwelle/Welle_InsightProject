import numpy as np

import tweepy

import textblob
from textstat.textstat import textstat
import HTMLParser

import secrets

auth = tweepy.OAuthHandler(secrets.consumer_key, secrets.consumer_secret) 
auth.set_access_token(secrets.access_token, secrets.access_token_secret) 
twitter_api = tweepy.API(auth)

def retrieve_examples(word=u"happy", ranks=[0,0,0]):

    text_list, tweet_list = twitter(word)

    url_list = build_url_list(tweet_list)
    html_list = get_html_list(url_list)

    polarity_list, subjectivity_list, readability_list = [[],[],[]]
    for text in text_list:
        polarity, subjectivity, readability = get_passage_scores(text)
        polarity_list.append(polarity)
        subjectivity_list.append(subjectivity)
        readability_list.append(readability)

    ranked_scores = rank_posts(polarity_list, subjectivity_list, readability_list, ranks)
    index_1, index_2, index_3 = (-ranked_scores).argsort()[:3]

    out_text = [text_list[index_1], text_list[index_2], text_list[index_3]]
    out_passages = [tweet_list[index_1], tweet_list[index_2], tweet_list[index_3]]
    out_html = [html_list[index_1], html_list[index_2], html_list[index_3]]

    ## possibly submit tweet.user.screen_name

    return out_text, out_html

def twitter(word):
    curs = tweepy.Cursor(twitter_api.search, q=word, lang="en", result_type="popular", 
        tweet_mode="extended", include_entities=True).items(100)
    tweet_list = []
    for tweet in curs: tweet_list.append(tweet) 

    text_list = []
    for tweet in tweet_list:
        if (not tweet.retweeted):         
            text = clean_tweet(tweet)
            text_list.append(text)

    return text_list, tweet_list

#Gets the text, sans links, hashtags, mentions, media, and symbols.
def clean_tweet(tweet):
    # Source: https://gist.github.com/timothyrenner/dd487b9fd8081530509c
    text = tweet.full_text

    html_parser = HTMLParser.HTMLParser()
    text = html_parser.unescape(text)

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
        
    return unicode(text.strip())

def get_url_list(tweet_list):
    def append_from_urls(tweet, url_list, appended):
        urls = tweet.entities['urls']
        for url in urls:
            if(u"twitter" in url['expanded_url']):
                url_list.append(url['expanded_url'])
                appended = True
                break
        return appended, url_list

    def get_url_from_media(tweet, url_list, appended):
        if (u"media" in tweet.entities.keys()):
            for media in tweet.entities['media']:
                if(u"expanded_url" in media.keys()):
                    url = media['expanded_url']
                    if (u"twitter" in url):
                        split_url = url.split('/')
                        if(u"photo" in split_url):
                            index = split_url.index(u"photo")
                            split_url = split_url[0:index]
                        elif(u"video" in split_url):
                            index = split_url.index(u"video")
                            split_url = split_url[0:index]
                        url = "/".join(split_url)
                        url_list.append(url)
                        appended = True
                        break
        return url_list, appended

    url_list = []
    appended_list = []
    for tweet in tweet_list:
        appended = False
        appended, url_list = append_from_urls(tweet, url_list, appended)
        if(not appended): url_list, appended = get_url_from_media(tweet, url_list, appended)
        appended_list.append(appended)

    return url_list, appended_list

def build_url_list(tweet_list):
    url_list = []

    for tweet in tweet_list:
        post_id = tweet.id_str
        user_name = tweet.author.screen_name
        url = u"http://twitter.com/" + user_name + u"/status/" + post_id
        url_list.append(url)
    return url_list

def get_html_list(url_list):
    html_list = []
    for url in url_list:
        html = twitter_api.get_oembed(url=url)['html']
        html_list.append(html)
    return html_list

def get_passage_scores(passage):
    readability = textstat.flesch_reading_ease(passage)
    polarity, subjectivity = textblob.TextBlob(passage).sentiment
    return polarity, subjectivity, readability

def rank_posts(polarity_list, subjectivity_list, readability_list, ranks):
    np_polarity = np.array(polarity_list)
    np_subj = np.array(subjectivity_list)
    np_read = np.array(readability_list)

    normalized_polarity = (np_polarity - np.mean(np_polarity)) / np.std(np_polarity)
    normalized_subj = (np_subj - np.mean(np_subj)) / np.std(np_subj)
    normalized_read = (np_read - np.mean(np_read)) / np.std(np_read)

    modified_normalized_polarity = modify_normalized_distribution(normalized_polarity, ranks[0])
    modified_normalized_subj = modify_normalized_distribution(normalized_subj, ranks[1])
    modified_normalized_read = modify_normalized_distribution(normalized_read, ranks[2])

    cumulative_score = modified_normalized_polarity + modified_normalized_subj + modified_normalized_read
    return cumulative_score

def get_text_indices(ranked_scores):
    def argpercentile(array, percentile):
        index = int(float(percentile) * (len(array) - 1) + 0.5)
        return np.argpartition(array, index)[index]

    index_1 = argpercentile(ranked_scores, 0.6)
    index_2 = argpercentile(ranked_scores, 0.8)
    index_3 = argpercentile(ranked_scores, 0.9)
    return index_1, index_2, index_3

def modify_normalized_distribution(normalized_array, rank):
    if(rank == 1): return normalized_array
    elif(rank == -1): return -1 * normalized_array
    elif(rank == 0):
        array = -1 * np.abs(normalized_array)
        renormalized_array = (array - np.mean(array)) / np.std(array)
        return renormalized_array