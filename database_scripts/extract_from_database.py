import os
import sys
import pickle
import random

import numpy as np

import readability

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('white')
sns.set_context('talk')

import tweepy
import HTMLParser
from textblob import TextBlob
from gensim.models.doc2vec import Doc2Vec
import ast

import model
import secrets
import twitter_utils

def gutenberg(word):
    word_object = model.Word.get_word_object(word)
    passages = word_object.passages
    passages_in_fiction = [passage for passage in passages if passage.parent_doc.doctype == 'book']
    text_list = [TextBlob(passage.get_paragraph()) for passage in passages_in_fiction]

    return passages_in_fiction, text_list

def newspaper(word):
    word_object = model.Word.get_word_object(word)
    passages = word_object.passages
    passages_in_newspaper = [passage for passage in passages if passage.parent_doc.doctype == 'article']
    text_list = [TextBlob(passage.get_paragraph()) for passage in passages_in_newspaper]

    return passages_in_newspaper, text_list

def get_metric_lists(passages):
    polarity_list = []
    subjectivity_list = []
    readability_list = []
    for passage in passages:
        polarity_list.append(passage.polarity)
        subjectivity_list.append(passage.subjectivity)
        readability_list.append(passage.readability)
    return polarity_list, subjectivity_list, readability_list

def tf_idf(text_list):
    from sklearn.feature_extraction.text import TfidfVectorizer
    model = TfidfVectorizer()
    result = model.fit_transform([str(text) for text in text_list])
    return result

def retrieve_examples(word, source, ranks):

    def modify_normalized_distribution(normalized_array, rank):
        if(rank == 1): return normalized_array
        elif(rank == -1): return -1 * normalized_array
        elif(rank == 0):
            array = -1 * np.abs(normalized_array)
            renormalized_array = (array - np.mean(array)) / np.std(array)
            return renormalized_array

    def rank_posts(polarity_list, subjectivity_list, readability_list, ranks):
        np_polarity = np.array(polarity_list)
        np_subj = np.array(subjectivity_list)
        np_read = np.array(readability_list)

        normalized_polarity = (np_polarity - np.mean(np_polarity)) / np.std(np_polarity)
        normalized_subj = (np_subj - np.mean(np_subj)) / np.std(np_subj)
        normalized_read = (np_read - np.mean(np_read)) / np.std(np_read)

        modified_normalized_polarity = modify_normalized_distribution(normalized_polarity, ranks[0])
        modified_normalized_subj = modify_normalized_distribution(normalized_subj, ranks[1])
        modified_normalized_read = modify_normalized_distribution(normalized_read, ranks[2])

        cumulative_score = modified_normalized_polarity + modified_normalized_subj + modified_normalized_read
        return cumulative_score

    def get_text_indices(ranked_scores):
        def argpercentile(array, percentile):
            index = int(float(percentile) * (len(array) - 1) + 0.5)
            return np.argpartition(array, index)[index]

        index_1 = argpercentile(ranked_scores, 0.6)
        index_2 = argpercentile(ranked_scores, 0.8)
        index_3 = argpercentile(ranked_scores, 0.9)
        return index_1, index_2, index_3

    if(source == 'twitter'):
        out_passages, out_html = twitter_utils.retrieve_examples(word, ranks)
        return out_passages
    elif(source == 'fiction'):
        passages, text = gutenberg(word)
    elif(source == 'news'):
        passages, text = newspaper(word)

    polarity_list, subjectivity_list, readability_list = get_metric_lists(passages)
    ranked_scores = rank_posts(polarity_list, subjectivity_list, readability_list, ranks)
    index_1, index_2, index_3 = get_text_indices(ranked_scores)

    out_passages = [passages[index_1], passages[index_2], passages[index_3]]

    return out_passages

def get_similar_passages(word, example_embedding, source):

    def cosine_similarity(v, M):
        return np.inner(v, M) / (np.linalg.norm(v) * np.linalg.norm(M, axis=1))

    passages = model.Word.get_word_object(word).passages
    if(source == 'fiction'): doctype = 'book'
    if(source == 'news'): doctype = 'article'
    passages = [passage for passage in passages if passage.parent_doc.doctype == doctype]

    embeddings = [passage.document_embedding for passage in passages]

    similarity_scores = cosine_similarity(ast.literal_eval(example_embedding), embeddings)
    index_1, index_2, index_3 = (-similarity_scores).argsort()[:3]

    return [passages[index_1], passages[index_2], passages[index_3]]

if __name__ == '__main__':
    
    word = sys.argv[0]
    twitter_text = twitter(word)
    gutenberg_text = gutenberg(word)
    newspaper_text = newspaper(word)

    out_dict = {}
    out_dict['twitter'] = [twitter_text] + get_metric_lists(twitter_text)
    out_dict['fiction'] = [gutenberg_text] + get_metric_lists(gutenberg_text)
    out_dict['news'] = [newspaper_text] + get_metric_lists(newspaper_text)

    out_text = twitter_text + gutenberg_text + newspaper_text

    polarity_list = [get_polarity(text_blob) for text_blob in out_text]
    subjectivity_list = [get_subjectivity(text_blob) for text_blob in out_text]
    readability_list = [get_readability(text_blob) for text_blob in out_text]