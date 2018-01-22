import numpy as np
import pandas as pd

import string

from gensim.models.doc2vec import TaggedDocument
from gensim.models.doc2vec import Doc2Vec

from textblob import TextBlob

import model

def generate_doc2vec_model(text_list):
    documents = []
    for index, text in enumerate(text_list):                                                                                        
        documents.append(TaggedDocument(words=TextBlob(text).words, tags=[u'Passage_'+str(index)]))  
    d2v_model = Doc2Vec(documents, size=100, window=8, min_count=5, workers=4)
    return d2v_model, documents

def get_similarity_matrix(model, documents):
    out_df = pd.DataFrame(index=range(len(documents)), columns=range(len(documents)))

    for index, document in enumerate(documents):
        temp_series = pd.Series(index=range(len(documents)), name=index)
        tokens = document.words
        new_vector = model.infer_vector(tokens)
        sims = model.docvecs.most_similar([new_vector], topn=len(documents))
        temp_df = pd.DataFrame(sims)
        indices = pd.DataFrame(temp_df[0].str.split('_').tolist(), columns=['SENT', 'Indices'])['Indices'].astype(int).tolist()
        out_df[index] = pd.Series(temp_df[1].values, index=indices, name=index)

    return out_df

def delete_all_chars(word, chars):
    for char in chars:
        word = word.replace(char, '')
    return word

if __name__ == '__main__':
    
    passages = model.Passage.objects()
    passage_text_list = [passage.passage_text for passage in passages]

    d2v_model, documents = generate_doc2vec_model(passage_text_list)

    for index, passage in enumerate(passages):
        passage.document_embedding = d2v_model.docvecs[index].tolist()
        passage.save()