import tweepy

import textblob
import HTMLParser

import secrets

auth = tweepy.OAuthHandler(secrets.consumer_key, secrets.consumer_secret) 
auth.set_access_token(secrets.access_token, secrets.access_token_secret) 
twitter_api = tweepy.API(auth)

def twitter(word):
    curs = tweepy.Cursor(twitter_api.search, q=word, lang="en", result_type="popular", 
        tweet_mode="extended", include_entities=True).items(100)
    tweet_list = []
    for tweet in curs: tweet_list.append(tweet) 

    text_list = []
    for tweet in tweet_list:
        if (not tweet.retweeted) and ('RT @' not in tweet.full_text):         
            text = clean_tweet(tweet)
            words = textblob.TextBlob(text)
            text_list.append(words)

    return text_list, tweet_list

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

def get_html_list(url_list):
    html_list = []
    for url in url_list:
        html = twitter_api.get_oembed(url=url)['html']
        html_list.append(html)
    return html_list

if __name__ == '__main__':

    text_list, tweet_list = twitter(u'happy')
    url_list, appended_list = get_url_list(tweet_list)
    html_list = get_html_list(url_list)
    short_text_list = [text for (appended, text) in zip(appended_list, text_list) if appended]
