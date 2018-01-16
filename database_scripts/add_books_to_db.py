import sys
import string

from datetime import datetime
from threading import Thread

import mongoengine

from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers
from gutenberg.query import get_etexts
from gutenberg.query import get_metadata

import model
import extract_metadata


if __name__ == '__main__':
	
    min_word_length = 4

    def process_book_wait(book_object):
        thread = Thread(target=process_book, args=(book_object,))
        thread.start()
        thread.join()

    def process_book(book_object):
        text = book_object.text
        paragraphs = text.split('\n\n')
        for paragraph_index, paragraph in enumerate(paragraphs):
            paragraph = paragraph.replace('\n\n', ' ')
            passage_object = model.Passage(parent_doc=book_object, paragraph_index=paragraph_index).save()
            for word in paragraph.split(' '):
                word = word.encode('ascii', 'ignore').translate(None, punctuation_droplist).lower()
                word_object = model.Word.get_word_object(word)
                if(word_object is not None):
                    word_object.update(add_to_set__passages=passage_object)

    print "Loading books..."
    tstart = datetime.now()

    punctuation_droplist = string.punctuation.replace("-", "")

    with open('books.txt', 'r') as f:
        books = []
        for line in f:
            books.append(int(line.rstrip()))

    for book in books:
        text = strip_headers(load_etext(book)).strip()
        metadata = extract_metadata.execute()
        title =  metadata[book]['title']
        author = metadata[book]['author']
        try:
            book_object = model.Parent_Document(text=text, title=title, author=author, url=title, doctype='book').save()
            process_book_wait(book_object)
        except mongoengine.NotUniqueError:
            print "Book " + title + " by " + author + " already in database. Book skipped. If you would like to reload, please first delete."
            continue
        print "Finished with " + title + " by " + author

    tend = datetime.now()
    print "Loaded books: Total time: " + str((tend-tstart).seconds)