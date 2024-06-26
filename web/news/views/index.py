"""
"""
from pathlib import Path

import bs4
import requests
import flask
import re
import news
from tensorflow import keras
import tensorflow as tf
import numpy as np
import keras.preprocessing.text as token

@news.app.route("/")
def show_index():
    return flask.render_template("index.html")



@news.app.route("/evaluation", methods=["POST"])
def show_evaluation():
    #Set max_len (got from shrink_model)
    max_len = 3073

    #Load the tokenizer from shrink_model
    with open("news/views/tokenizer.json", "r") as json_file:
        tokenizer_json = json_file.read()
        tokenizer = token.tokenizer_from_json(tokenizer_json)


    #Load in the exported model
    model = tf.keras.models.load_model("news/views/shrink_model.h5")
    
    #Run model on text Snippet
    snippet = flask.request.form["snippet"]
    snippet = clean_text([snippet])
    test_sequences = tokenizer.texts_to_sequences(snippet)
    test = keras.preprocessing.sequence.pad_sequences(test_sequences, maxlen=max_len, padding='post', truncating='post')

    pred = model.predict(test)
    
    
    # The label
    pred_index = np.argmax(pred)

    # predict value
    #pred_label = pred[0, pred_index]

    # Sets the label
    label = ""
    if pred_index == 0:
        label = "Potentially Misleading"
    elif pred_index == 1:
        label = "Unsure"
    elif pred_index == 2:
        label = "Potentially true"

    # Context json used for populating page
    context = {"prediction": label}

    return flask.render_template("evaluation.html", **context)


@news.app.route("/result", methods=["POST"])
def show_result():
    #Set max_len (got from shrink_model)
    max_len = 3073
    link = flask.request.form["link"]
    try:
        result = requests.get(link)
        content = result.text
    
        soup = bs4.BeautifulSoup(content,'html.parser')
        text = soup.text
        text =  text = re.sub(r"[^a-zA-Z0-9.!? ]+", "", text).casefold()
        text = re.split(r"(?<=[.!?]) +", text)
        
        cleaned_text = []
        for sentence in text:
            cleaned_add = ' '.join(sentence.split())
            cleaned_text.append(cleaned_add)

        
        #Hard coded for https://www.cnn.com/2024/04/10/health/pfas-drinking-water-standard/index.html
        # There is a lot of random noise, so may want to carefully select which websites are used.
        random_snippet = cleaned_text[9]
        #random_snippet = cleaned_text[np.random.randint(len(cleaned_text))]

        #Load the tokenizer from shrink_model
        with open("news/views/tokenizer.json", "r") as json_file:
            tokenizer_json = json_file.read()
            tokenizer = token.tokenizer_from_json(tokenizer_json)


        #Load in the exported model
        model = tf.keras.models.load_model("news/views/shrink_model.h5")
        snippet = clean_text([random_snippet])
        test_sequences = tokenizer.texts_to_sequences(snippet)
        test = keras.preprocessing.sequence.pad_sequences(test_sequences, maxlen=max_len, padding='post', truncating='post')

        pred = model.predict(test)

        # The label
        pred_index = np.argmax(pred)

        # Sets the label
        label = ""
        if pred_index == 0:
            label = "Potentially Misleading"
        elif pred_index == 1:
            label = "Unsure"
        elif pred_index == 2:
            label = "Potentially true"

        # Context json used for populating page
        context = {"prediction": label,
                   "sentence":random_snippet}

        return flask.render_template("result.html", **context)
    except Exception as e:
        print(e)
        return flask.redirect(flask.url_for("show_index"))
    
@news.app.route("/about")
def show_about():
    return flask.render_template("about.html")
    
def clean_text(text):
    if not isinstance(text, str):
        return text
    clean_text = text.lower()
    clean_text = re.sub(r'[^\w\s]', '', clean_text)
    return clean_text