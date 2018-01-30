import pandas as pd
import psycopg2

from flask import request
from flask import render_template

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

import database_scripts as db
from webapp import app

import ast

@app.route('/')
@app.route('/', methods=['POST'])
def index():
    if request.method != "POST":
        return render_template("index.html")
    
    else:
        try:
          if request.form['mode'] == 'first_query':
              query = request.form['query'].lower()
              tone = request.form['tone']
              objectivity = request.form['objectivity']
              complexity = request.form['complexity']
              source = request.form['source']
              ranks=[int(tone), -1*int(objectivity), -1*int(complexity)] # actual terms are subjectivity and readability, so flip
              passage_list = db.retrieve_examples(query, source, ranks)
              return render_template("index.html", passage_list=passage_list, word=query, source=source, ranks=ranks)
          
          elif request.form['mode'] == 'get_similar':
              word = request.form['word'].lower()
              embedding = request.form['embedding']
              source = request.form['source']
              selected_passage = request.form['doc_id']
              ranks = ast.literal_eval(request.form['ranks']) 
              passage_list = db.get_similar_passages(word, embedding, source, selected_passage)
              return render_template("index.html", passage_list=passage_list, word=word, source=source, ranks=ranks)        
        except:
          return render_template("index.html", source="error")