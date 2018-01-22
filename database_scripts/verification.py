import pandas as pd

import sklearn as skl
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import model

def create_Xy(parent_docs):
    X = []
    y = []
    for doc in parent_docs:
        X.extend([list(passage.document_embedding) for passage in doc.passages])
        y.extend([doc.unique_field]*len(doc.passages))
    X = pd.DataFrame(X)
    y = pd.Series(pd.factorize(y)[0])
    return X,y

if __name__ == '__main__':
    parent_docs = model.Parent_Document.objects()
    X,y = create_Xy(parent_docs)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=4512)

    from sklearn.naive_bayes import GaussianNB
    nb = GaussianNB()
    nb.fit(X_train, y_train)
    y_pred = nb.predict(X_test)
    accuracy_score(y_test, y_pred)

    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=100, n_jobs=3)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    accuracy_score(y_test, y_pred)

    # from sklearn.model_selection import GridSearchCV
    # rf = RandomForestClassifier(n_estimators=100, n_jobs=3)
    # param_grid = {'max_features': ['sqrt', 'log2', None], 'min_samples_split': np.geomspace(0.0001, 0.99, num=12)}
    # param_grid = {'max_features': ['sqrt'], 'min_samples_split': np.linspace(0.01, 0.99, num=3)}
    # clf = GridSearchCV(rf, param_grid)
    # clf.fit(X,y)
