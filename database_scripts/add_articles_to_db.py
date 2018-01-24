import sys
import random
import datetime

import string
import re
from threading import Thread

import textacy
import textblob

import newspaper

import model

def process_article_wait(document_object, punctuation_droplist):
    thread = Thread(target=process_article, args=(document_object,punctuation_droplist))
    thread.start()
    thread.join()

def process_article(document_object, punctuation_droplist):
    
    def store_passage_object(passage, document_object):
        polarity, subjectivity, readability = get_passage_scores(passage)
        passage_object = model.Passage(parent_doc=document_object, passage_text=passage, polarity=polarity,
            subjectivity=subjectivity, readability=readability, passage_index=index).save()
        return passage_object

    def update_word_object(passage, punctuation_droplist):
        for word in passage.split(' '):
            word = delete_all_chars(word, punctuation_droplist).lower()
            word_object = model.Word.get_word_object(word)
            if(word_object is not None):
                word_object.update(add_to_set__passages=passage_object)

    text = document_object.text
    passages = get_passages_from_text(text, document_object)
    passage_object_list = []
    for index, passage in enumerate(passages):
        passage_object = store_passage_object(passage, document_object)
        passage_object_list.append(passage_object)
        update_word_object(passage, punctuation_droplist)
    document_object.passages = passage_object_list
    document_object.save()

def get_passages_from_text(text, document_object):
    sentences = split_into_sentences(text)
    passages = construct_passages(sentences, document_object)
    return passages

def split_into_sentences(text):
    # function modified from https://stackoverflow.com/questions/4576077/python-split-text-on-sentences
    caps = "([A-Z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(". ",".<stop>")
    text = text.replace("? ","?<stop>")
    text = text.replace("! ","!<stop>")
    text = text.replace("\"?","?\"")
    text = text.replace("\"!","!\"")
    text = text.replace("\".",".\"")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences    

def construct_passages(sentences, document_object):
    def preprocess_first_sentences(sentences):
        skip_list = []
        for index, sentence in enumerate(sentences):
            if(u"(C)" in sentence): skip_list.append(index)
            if(u"Image copyright" in sentence): skip_list.append(index)
            if(u"Image caption" in sentence): skip_list.append(index)
            if(u"Getty Images" in sentence): skip_list.append(index)
            if(u"Media playback" in sentence): skip_list.append(index)
            if(document_object.title in sentence): skip_list.append(index)
        return skip_list

    passages = []
    skip_list = preprocess_first_sentences(sentences)
    temp_passage = ""

    for index, sentence in enumerate(sentences):
        if(index in skip_list): continue
        temp_passage = temp_passage + " " + sentence
        if((len(temp_passage) >= 200) and (len(temp_passage) <= 750)):
            passages.append(temp_passage.strip())
            temp_passage = ""
        elif(len(temp_passage) < 200): continue
        elif(len(temp_passage) > 750):
            temp_passage = ""
    return passages

def get_passage_scores(passage):
    doc = textacy.Doc(passage, lang=u"en_core_web_sm")
    textstats = textacy.TextStats(doc)
    readability = textstats.flesch_readability_ease
    polarity, subjectivity = textblob.TextBlob(passage).sentiment
    return polarity, subjectivity, readability

def delete_all_chars(word, chars):
    for char in chars:
        word = word.replace(char, '')
    return word

if __name__ == '__main__':

    url = sys.argv[1]

    tstart = datetime.datetime.now()

    min_word_length = 4
    punctuation_droplist = string.punctuation

    try: 
        website = newspaper.build(url, memoize_articles=False, language='en')
    except:
        print("Invalid url")
        sys.exit()

    print("Loading articles...")
    print("Found " + str(len(website.articles)) + " articles")

    articles = website.articles

    for article in articles:
        article.download()
        article.parse()
        text = article.text
        title =  article.title
        article_url = article.url

        if(len(text) < 200): continue

        try:
            document_object = model.Parent_Document(text=text, title=title, unique_field=article_url, author=url, doctype='article').save()
            process_article_wait(document_object, punctuation_droplist)
        except model.NotUniqueError:
            print("Article " + article_url + " already in database. Article skipped. If you would like to reload, please first delete.")
            continue
        except:
            print("Skipping article " + article_url + ". Reason unknown")
        print("Finished with " + article_url)

    tend = datetime.datetime.now()
    print("Loaded articles: Total time: " + str((tend-tstart).seconds))
