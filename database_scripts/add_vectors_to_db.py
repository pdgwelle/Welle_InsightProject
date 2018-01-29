import sys
import pickle

import numpy as np
import pandas as pd

import string

from gensim.models.doc2vec import TaggedDocument
from gensim.models.doc2vec import Doc2Vec

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

from textblob import TextBlob

import model

def generate_doc2vec_model(text_list):
    documents = []
    for index, text in enumerate(text_list):                                                                                        
        documents.append(TaggedDocument(words=TextBlob(text).words, tags=[u'Passage_'+str(index)]))  
    d2v_model = Doc2Vec(documents, size=100, window=8, min_count=5, workers=4)
    return d2v_model, documents

def generate_tf_idf_model(text_list):
    tf_model = TfidfVectorizer()
    result = tf_model.fit_transform([text for text in text_list])
    return tf_model, result

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
    
    if(sys.argv[1] == 'doc2vec'):
        print("Training model...")
        passages = model.Passage.objects()
        passage_text_list = [passage.passage_text for passage in passages]

        d2v_model, documents = generate_doc2vec_model(passage_text_list)

        print("Storing passage vectors...")
        for index, passage in enumerate(passages):
            passage.document_embedding_doc2vec = d2v_model.docvecs[index].tolist()
            passage.save()

        d2v_model.save('assets/d2v_model')

    elif(sys.argv[1] == 'tf-idf'):
        print("Training model...")
        passages = model.Passage.objects()
        passage_text_list = [passage.passage_text for passage in passages]

        tf_model, result = generate_tf_idf_model(passage_text_list)
        svd = TruncatedSVD(n_components=100)
        svd.fit(result.transpose())
        reduced_vector = svd.components_

        print("Storing passage vectors...")
        for index, passage in enumerate(passages):
            passage.document_embedding_tfidf = reduced_vector[:,index].tolist()
            passage.save()

    elif(sys.argv[1] == 'word2vec'):

        print("Reading in vectors...")
        with open("assets/GoogleNews-vectors-negative300.pcl") as f:
            gnews_dict = pickle.load(f)

        passages = model.Passage.objects()

        print("Writing average word2vec vectors to df")
        for index, passage in enumerate(passages):
            passage_text = passage.passage_text
            vector_sum = np.zeros(300)
            n_words = 0
            for word in TextBlob(passage_text).words:
                vector = gnews_dict.get(word)
                if vector: 
                    vector_sum+=vector
                    n_words+=1
            if(n_words > 0): passage.document_embedding_word2vec = (vector_sum / float(n_words)).tolist()
            else: passage.document_embedding_word2vec = vector_sum.tolist()
            passage.save()