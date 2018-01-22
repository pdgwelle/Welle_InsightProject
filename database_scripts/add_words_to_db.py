import string
from datetime import datetime

from nltk.corpus import stopwords

import model

def delete_all_chars(word, chars):
    for char in chars:
        word = word.replace(char, '')
    return word

if __name__ == '__main__':

    min_word_length = 4

    print "Loading words..."
    tstart = datetime.now()

    model.Word.objects.delete()

    stop_words = set(stopwords.words('english'))
    stop_words = map(lambda x: delete_all_chars(x, string.punctuation), stop_words)

    with open('words.txt', 'r') as f:
        words = []
        for line in f:
            line = line.strip().lower()
            if((len(line) >= min_word_length) and (line not in stop_words)):
                word_object = model.Word(word=line).save()

    tend = datetime.now()
    print "Loaded words: Total time: " + str((tend-tstart).seconds)

