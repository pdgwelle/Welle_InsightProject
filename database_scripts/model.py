from mongoengine import *

db = connect('ftm_constucted_passages_long')

class Parent_Document(Document):
    text = StringField()
    title = StringField()
    author = StringField()
    doctype = StringField()
    unique_field = StringField(unique=True)
    passages = ListField(ReferenceField('Passage'))

    def __repr__(self):
        return '<Parent_Document - Title: %r Author: %r>' % (self.title, self.author)

class Passage(Document):
    parent_doc = ReferenceField(Parent_Document, reverse_delete_rule=CASCADE)
    passage_text = StringField()
    polarity = FloatField()
    subjectivity = FloatField()
    readability = FloatField()
    passage_index = LongField()
    document_embedding_doc2vec = ListField(FloatField())
    document_embedding_tfidf = ListField(FloatField())
    document_embedding_word2vec = ListField(FloatField())
    document_embedding = ListField(FloatField())

    def get_paragraph(self):
        return self.passage_text

    def __repr__(self):
        return '<Passage - Parent Document: %r>' % (self.parent_doc.title)

class Word(Document):

    @staticmethod
    def get_word_object(word):
        min_word_length = 4
        if(len(word) >= min_word_length):
            word_list = Word.objects(word=word).first()
            if(word_list is not None):
                return word_list
                
    word = StringField()
    passages = ListField(ReferenceField(Passage, reverse_delete_rule=PULL))

    meta = {'indexes': ['$word', '#word']}

    def __repr__(self):
        return '<Word: %r>' % (self.word)

def get_word_stats():
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    words = Word.objects()
    n_passages = pd.Series([len(word.passages) for word in words]).sort_values(ascending=False)
    n_passages_short = n_passages[n_passages>2]
    percent_covered = len(n_passages_short) / float(len(n_passages))
    plt.bar(range(len(n_passages_short)), n_passages_short)
    plt.text(.70*len(n_passages_short),.75*np.max(n_passages_short),unicode("COVERAGE = " + str(int(percent_covered*100)) + '%'))
    plt.text(.70*len(n_passages_short),.70*np.max(n_passages_short),unicode("MEDIAN = " + str(np.median(n_passages_short))))
    plt.text(.70*len(n_passages_short),.65*np.max(n_passages_short),unicode("MAX = " + str(np.max(n_passages_short))))
    plt.show()