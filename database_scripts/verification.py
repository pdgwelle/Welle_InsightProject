import sys

import numpy as np
import pandas as pd

import sklearn as skl
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import model

def create_Xy(parent_docs, doctype):
    X = []
    y = []
    for doc in parent_docs:
        X.extend([list(passage.document_embedding) for passage in doc.passages])
        if(doctype == 'book'): 
            y.extend([doc.unique_field]*len(doc.passages))
        else:
            y.extend([doc.author]*len(doc.passages))
    X = pd.DataFrame(X)
    y = pd.Series(pd.factorize(y)[0])
    return X,y

if __name__ == '__main__':
    if(len(sys.argv) == 1):
        print("Please add doctype of either 'article' or 'book'")
        sys.exit()

    doctype = sys.argv[1]
    if(doctype not in ['article', 'book']):
        print("Doctype not 'article' or 'book'")
        sys.exit()

    parent_docs = model.Parent_Document.objects(doctype=doctype)

    X,y = create_Xy(parent_docs, doctype)

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
    # param_grid = {'max_features': ['sqrt', 'log2', None], 'min_samples_split': np.geomspace(0.0001, 0.99, num=12)}
    # param_grid = {'max_features': ['sqrt'], 'min_samples_split': np.linspace(0.01, 0.99, num=3)}
    # clf = GridSearchCV(rf, param_grid)
    # clf.fit(X,y)