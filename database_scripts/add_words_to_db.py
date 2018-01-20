from datetime import datetime

import model

if __name__ == '__main__':

    min_word_length = 4

    print "Loading words..."
    tstart = datetime.now()

    model.Word.objects.delete()

    with open('words.txt', 'r') as f:
        words = []
        for line in f:
            line = line.strip().lower()
            if(len(line) >= min_word_length):
                word_object = model.Word(word=line).save()

    tend = datetime.now()
    print "Loaded words: Total time: " + str((tend-tstart).seconds)

