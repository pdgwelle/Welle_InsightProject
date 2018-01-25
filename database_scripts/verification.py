import sys

import numpy as np
import pandas as pd

import sklearn as skl
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import model

def create_Xy(parent_docs, doctype, mode):
    X = []
    y = []
    for doc in parent_docs:
        if(mode == "doc2vec"):
            X.extend([list(passage.document_embedding_doc2vec) for passage in doc.passages])
        elif(mode == 'tf-idf'):
            X.extend([list(passage.document_embedding_tfidf) for passage in doc.passages])
        elif(mode == 'word2vec'):
            X.extend([list(passage.document_embedding_word2vec) for passage in doc.passages])

        if(doctype == 'book'): 
            y.extend([doc.unique_field]*len(doc.passages))
        else:
            y.extend([doc.author]*len(doc.passages))

    X = pd.DataFrame(X)
    y = pd.Series(pd.factorize(y)[0])
    return X,y

if __name__ == '__main__':
    if((len(sys.argv) == 1) | (len(sys.argv) == 2)):
        print("Please add doctype of either 'article' or 'book' as well as algorithm, such as doc2vec or tf-idf")
        print("Example call: python verification.py article doc2vec")
        sys.exit()

    doctype = sys.argv[1]
    if(doctype not in ['article', 'book']):
        print("Doctype not 'article' or 'book'")
        sys.exit()

    mode = sys.argv[2]
    if(mode not in ['doc2vec', 'tf-idf', 'word2vec']):
        print("Algorithm not 'doc2vec', 'word2vec' or 'tf-idf'")
        sys.exit()

    parent_docs = model.Parent_Document.objects(doctype=doctype)

    X,y = create_Xy(parent_docs, doctype, mode)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=4512)

    from sklearn.naive_bayes import GaussianNB
    nb = GaussianNB()
    nb.fit(X_train, y_train)
    y_pred = nb.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print("Naive Bayes accuracy " + str(accuracy))

    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=100, n_jobs=3)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print("Random Forest accuracy " + str(accuracy))

    # from sklearn.model_selection import GridSearchCV
    # rf = RandomForestClassifier(n_estimators=100, n_jobs=3)
    # param_grid = {'max_features': ['sqrt', 'log2', None], 'min_samples_split': np.geomspace(0.000001, 0.5, num=12)}
    # #param_grid = {'max_features': ['sqrt'], 'min_samples_split': np.linspace(0.01, 0.99, num=3)}
    # clf = GridSearchCV(rf, param_grid)
    # clf.fit(X,y)

