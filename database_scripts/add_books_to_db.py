import sys

import re
import string

from datetime import datetime
from threading import Thread

import mongoengine

import textacy
import textblob

from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers
from gutenberg.query import get_etexts
from gutenberg.query import get_metadata

import model
import extract_metadata

def process_book_wait(book_object, punctuation_droplist):
    thread = Thread(target=process_book, args=(book_object,punctuation_droplist))
    thread.start()
    thread.join()

def process_book(book_object, punctuation_droplist):

    def store_passage_object(passage):
        polarity, subjectivity, readability = get_passage_scores(passage)
        passage_utf8 = passage.encode('utf-8')
        passage_object = model.Passage(parent_doc=book_object, passage_text=passage_utf8, polarity=polarity,
            subjectivity=subjectivity, readability=readability, passage_index=index).save()
        return passage_object

    def update_word_object(passage, punctuation_droplist):
        for word in passage.split(' '):
            word = delete_all_chars(word, punctuation_droplist).lower()
            word_object = model.Word.get_word_object(word)
            if(word_object is not None):
                word_object.update(add_to_set__passages=passage_object)

    text = book_object.text
    passages = get_passages_from_text(text, book_object)
    passage_object_list = []
    for index, passage in enumerate(passages):
        passage_object = store_passage_object(passage)
        passage_object_list.append(passage_object)
        update_word_object(passage, punctuation_droplist)
    book_object.passages = passage_object_list
    book_object.save()

def get_passages_from_text(text, book_object):
    sentences = split_into_sentences(text)
    passages = construct_passages(sentences, book_object)
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

def construct_passages(sentences, book_object):
    def preprocess_first_sentences(sentences, n=10):
        skip_list = []
        for index, sentence in enumerate(sentences[0:n]):
            if(u"(C)" in sentence): skip_list.append(index)
            if(book_object.title in sentence): skip_list.append(index)
            for author_name in book_object.author.split(','):
                if(author_name in sentence): skip_list.append(index)
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
	
    min_word_length = 4

    print "Loading books..."
    tstart = datetime.now()

    punctuation_droplist = string.punctuation

    with open('books.txt', 'r') as f:
        books = []
        for line in f:
            books.append(int(line.rstrip()))

    metadata = extract_metadata.execute()
    for book in books:
        text = strip_headers(load_etext(book)).strip()
        text = text.replace('\n\n', '') # get rid of paragraph breaks
        text = text.replace('\n', ' ') # get rid of arbitrary newlines
        title =  metadata[book]['title']
        author = metadata[book]['author']
        try:
            text_utf8 = text.encode('utf-8')
            title_utf8 = title.encode('utf-8')
            author_utf8 = author.encode('utf-8')
            doctype_utf8 = u'book'.encode('utf-8')
            book_object = model.Parent_Document(text=text_utf8, title=title_utf8, author=author_utf8, doctype=doctype_utf8,     unique_field=title_utf8).save()
            process_book_wait(book_object, punctuation_droplist)
        except mongoengine.NotUniqueError:
            print "Book " + title + " by " + author + " already in database. Book skipped. If you would like to reload, please first delete."
            continue
        print "Finished with " + title + " by " + author

    tend = datetime.now()
    print "Loaded books: Total time: " + str((tend-tstart).seconds)