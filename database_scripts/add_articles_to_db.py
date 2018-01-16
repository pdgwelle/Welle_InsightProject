import sys

import string
from threading import Thread

import random
import datetime

import newspaper

import model

def process_article_wait(document_object):
    thread = Thread(target=process_article, args=(document_object,))
    thread.start()
    thread.join()

def process_article(document_object):
    text = document_object.text
    paragraphs = text.split('\n\n')
    for paragraph_index, paragraph in enumerate(paragraphs):
        paragraph = paragraph.replace('\n\n', ' ')
        passage_object = model.Passage(parent_doc=document_object, paragraph_index=paragraph_index).save()
        for word in paragraph.split(' '):
            word = word.encode('ascii', 'ignore').translate(None, punctuation_droplist).lower()
            word_object = model.Word.get_word_object(word.decode())
            if(word_object is not None):
                word_object.update(add_to_set__passages=passage_object)

if __name__ == '__main__':

    url = sys.argv[1]

    tstart = datetime.datetime.now()

    min_word_length = 4
    punctuation_droplist = bytearray(string.punctuation.replace("-", ""), 'utf-8')

    try: 
        website = newspaper.build(url, memoize_articles=False, language='en')
    except:
        print("Invalid url")
        sys.exit()

    print("Loading articles...")
    print("Found " + str(len(website.articles)) + " articles")

    # if(len(website.articles) > 100):
    #     articles = random.sample(website.articles, k=100)
    # else:
    #     articles = website.articles

    articles = website.articles

    for article in articles:
        article.download()
        article.parse()
        text = article.text
        title =  article.title
        url = article.url

        if(len(text) < 30): continue

        try:
            document_object = model.Parent_Document(text=text, title=title, url=url, doctype='article').save()
            process_article_wait(document_object)
        except model.mongoengine.NotUniqueError:
            print("Article " + url + " already in database. Article skipped. If you would like to reload, please first delete.")
            continue
        except:
            print("Skipping article " + url + ". Reason unknown")
        print("Finished with " + url)

    tend = datetime.datetime.now()
    print("Loaded articles: Total time: " + str((tend-tstart).seconds))
