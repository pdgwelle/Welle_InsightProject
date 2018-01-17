from mongoengine import *

db = connect('ftm')

class Parent_Document(Document):
    text = StringField()
    title = StringField()
    author = StringField()
    doctype = StringField()
    url = StringField(unique=True)

    def get_paragraph(self, paragraph_index):
        paragraphs = self.text.split('\n\n')
        if((paragraph_index >= len(paragraphs)) | (paragraph_index < 0)):
            return ''
        else:
            return paragraphs[paragraph_index].replace('\n', ' ')

    def __repr__(self):
        return '<Parent_Document - Title: %r Author: %r>' % (self.title, self.author)

class Passage(Document):
    parent_doc = ReferenceField(Parent_Document, reverse_delete_rule=CASCADE)
    paragraph_index = LongField()

    def get_paragraph(self, offset=0):
        return self.parent_doc.get_paragraph(self.paragraph_index + offset)

    def __repr__(self):
        return '<Passage - Parent Document: %r Paragraph: %r>' % (self.parent_doc.title, self.paragraph_index)

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
