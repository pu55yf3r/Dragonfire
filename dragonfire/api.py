#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
.. module:: api
    :platform: Unix
    :synopsis: the API of Dragonfire that contains the endpoints.

.. moduleauthor:: Mehmet Mert Yıldıran <mert.yildiran@bil.omu.edu.tr>
"""

import hug  # Embrace the APIs of the future
from hug_middleware_cors import CORSMiddleware  # Middleware for allowing CORS (cross-origin resource sharing) requests from hug servers
import waitress  # A production-quality pure-Python WSGI server with very acceptable performance
from threading import Thread  # Thread-based parallelism
import json  # JSON encoder and decoder
from dragonfire.config import Config  # Credentials for the database connection
from dragonfire.arithmetic import arithmetic_parse  # Submodule of Dragonfire to analyze arithmetic expressions
import wikipedia as wikipedia_lib  # Python library that makes it easy to access and parse data from Wikipedia
import re  # Regular expression operations
import youtube_dl  # Command-line program to download videos from YouTube.com and other video sites
import pymysql  # Pure Python MySQL Client
from random import choice  # Generate pseudo-random numbers


@hug.authentication.token
def token_authentication(token):
    """Method to compare the given token with precomputed token.

    Args:
        token (str):  API token.

    Returns:
        bool.  The return code::

            True -- The token is correct!
            False -- The token is invalid!
    """

    if token == precomptoken:
        return True


# Natural Language Processing realted API endpoints START

@hug.post('/tag', requires=token_authentication)
def tagger_end(text):
    """**Endpoint** to return **POS Tagging** result of the given text.

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    return json.dumps(tagger(text), indent=4)


def tagger(text):
    """Method to encapsulate **POS Tagging** process.

    Args:
        text (str):  Text.

    Returns:
        (list) of (dict)s:  List of dictionaries.
    """

    data = []
    doc = nlp(text)
    for token in doc:
        parse = {
            'text': token.text,
            'lemma': token.lemma_,
            'pos': token.pos_,
            'tag': token.tag_,
            'dep': token.dep_,
            'shape': token.shape_,
            'is_alpha': token.is_alpha,
            'is_stop': token.is_stop
            }
        data.append(parse)
    return data


@hug.post('/dep', requires=token_authentication)
def dependency_parser_end(text):
    """**Endpoint** to return **Dependency Parse** result of the given text.

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    return json.dumps(dependency_parser(text), indent=4)


def dependency_parser(text):
    """Method to encapsulate **Dependency Parse** process.

    Args:
        text (str):  Text.

    Returns:
        (list) of (dict)s:  List of dictionaries.
    """

    data = []
    doc = nlp(text)
    for chunk in doc.noun_chunks:
        parse = {
            'text': chunk.text,
            'root_text': chunk.root.text,
            'root_dep': chunk.root.dep_,
            'root_head_text': chunk.root.head.text,
        }
        data.append(parse)
    return data


@hug.post('/ner', requires=token_authentication)
def entity_recognizer_end(text):
    """**Endpoint** to return **Named Entity Recognition** result of the given text.

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    return json.dumps(entity_recognizer(text), indent=4)


def entity_recognizer(text):
    """Method to encapsulate **Named Entity Recognition** process.

    Args:
        text (str):  Text.

    Returns:
        (list) of (dict)s:  List of dictionaries.
    """

    data = []
    doc = nlp(text)
    for ent in doc.ents:
        parse = {
            'text': ent.text,
            'start_char': ent.start_char,
            'end_char': ent.end_char,
            'label': ent.label_,
        }
        data.append(parse)
    return data


@hug.post('/token', requires=token_authentication)
def tokenizer_end(text):
    """**Endpoint** to **tokenize** the given text.

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    return json.dumps(tokenizer(text), indent=4)


def tokenizer(text):
    """Method to encapsulate **tokenization** process.

    Args:
        text (str):  Text.

    Returns:
        (list) of (dict)s:  List of dictionaries.
    """

    data = []
    doc = nlp(text)
    for token in doc:
        data.append(token.text)
    return data


@hug.post('/sent', requires=token_authentication)
def sentence_segmenter_end(text):
    """**Endpoint** to return **Sentence Segmentation** result of the given text.

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    return json.dumps(sentence_segmenter(text), indent=4)


def sentence_segmenter(text):
    """Method to encapsulate **Sentence Segmentation** process.

    Args:
        text (str):  Text.

    Returns:
        (list) of (dict)s:  List of dictionaries.
    """

    data = []
    doc = nlp(text)
    for sent in doc.sents:
        data.append(sent.text)
    return data


# All-in-One NLP
@hug.post('/cmd', requires=token_authentication)
def cmd(text):
    """Serves the **all Natural Language Processing features** (parsers) of :mod:`spacy` in a single **endpoint**.

    Combines the results of these methods into a single JSON document:

     - :func:`dragonfire.api.tagger` method (**POS Tagging**)
     - :func:`dragonfire.api.dependency_parser` method (**Dependency Parse**)
     - :func:`dragonfire.api.entity_recognizer` method (**Named Entity Recognition**)

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    data = []
    sents = sentence_segmenter(text)
    for sent in sents:
        sent_data = {}
        sent_data['tags'] = tagger(sent)
        sent_data['deps'] = dependency_parser(sent)
        sent_data['ners'] = entity_recognizer(sent)
        data.append(sent_data)
    return json.dumps(data, indent=4)

# Natural Language Processing realted API endpoints END


# Directly on server-side Q&A related API endpoints START

@hug.post('/math', requires=token_authentication)
def math(text):
    """**Endpoint** to return the response of :func:`dragonfire.arithmetic.arithmetic_parse` function.

    Args:
        text (str):  Text.

    Returns:
        JSON document.
    """

    response = arithmetic_parse(text)
    if not response:
        response = ""
    return json.dumps(response, indent=4)


@hug.post('/learn', requires=token_authentication)
def learn(text, user_id):
    """**Endpoint** to return the response of :func:`dragonfire.learn.Learner.respond` method.

    Args:
        text (str):         Text.
        user_id (int):      User's ID.

    Returns:
        JSON document.
    """

    response = learner.respond(text, is_server=True, user_id=user_id)
    if not response:
        response = ""
    return json.dumps(response, indent=4)


@hug.post('/omni', requires=token_authentication)
def omni(text, gender_prefix):
    """**Endpoint** to return the answer of :func:`dragonfire.omniscient.Omniscient.respond` method.

    Args:
        text (str):             Text.
        gender_prefix (str):    Prefix to address/call user when answering.

    Returns:
        JSON document.
    """

    answer = omniscient.respond(text, userin=userin, user_prefix=gender_prefix, is_server=True)
    if not answer:
        answer = ""
    return json.dumps(answer, indent=4)


@hug.post('/deep', requires=token_authentication)
def deep(text, gender_prefix):
    """**Endpoint** to return the response of :func:`dragonfire.conversational.DeepConversation.respond` method.

    Args:
        text (str):             Text.
        gender_prefix (str):    Prefix to address/call user when answering.

    Returns:
        JSON document.
    """

    answer = dc.respond(text, user_prefix=gender_prefix)
    return json.dumps(answer, indent=4)


# All-in-One Answering
@hug.post('/answer', requires=token_authentication)
def answer(text, gender_prefix, user_id):
    """Serves the **all Q&A related API endpoints** in a single **endpoint**.

    Combines the results of these methods into a single JSON document:

     - :func:`dragonfire.arithmetic.arithmetic_parse` function
     - :func:`dragonfire.learn.Learner.respond` method
     - :func:`dragonfire.omniscient.Omniscient.respond` method
     - :func:`dragonfire.conversational.DeepConversation.respond` method

    Args:
        text (str):             Text.
        gender_prefix (str):    Prefix to address/call user when answering.
        user_id (int):          User's ID.

    Returns:
        JSON document.
    """

    answer = arithmetic_parse(text)
    if not answer:
        answer = learner.respond(text, is_server=True, user_id=user_id)
        if not answer:
            answer = omniscient.respond(text, userin=userin, user_prefix=gender_prefix, is_server=True)
            if not answer:
                answer = dc.respond(text, user_prefix=gender_prefix)
    return json.dumps(answer, indent=4)

# Directly on server-side Q&A related API endpoints END


@hug.post('/wikipedia', requires=token_authentication)
def wikipedia(query, gender_prefix):
    """**Endpoint** to make a **Wikipedia search** and return its **text content**.

    Args:
        query (str):            Search query.
        gender_prefix (str):    Prefix to address/call user when answering.

    Returns:
        JSON document.
    """

    response = ""
    url = ""
    wikiresult = wikipedia_lib.search(query)
    if len(wikiresult) == 0:
        response = "Sorry, " + gender_prefix + ". But I couldn't find anything about " + query + " in Wikipedia."
    else:
        wikipage = wikipedia_lib.page(wikiresult[0])
        wikicontent = "".join([
            i if ord(i) < 128 else ' '
            for i in wikipage.content
        ])
        wikicontent = re.sub(r'\([^)]*\)', '', wikicontent)
        response = " ".join(sentence_segmenter(wikicontent)[:3])
        url = wikipage.url
    data = {}
    data['response'] = response
    data['url'] = url
    return json.dumps(data, indent=4)


@hug.post('/youtube', requires=token_authentication)
def youtube(query, gender_prefix):
    """**Endpoint** to make a **YouTube search** and return the **video title** and **URL**.

    Args:
        query (str):            Search query.
        gender_prefix (str):    Prefix to address/call user when answering.

    Returns:
        JSON document.
    """

    response = ""
    url = ""
    info = youtube_dl.YoutubeDL({}).extract_info('ytsearch:' + query, download=False, ie_key='YoutubeSearch')
    if len(info['entries']) > 0:
        response = info['entries'][0]['title']
        url = "https://www.youtube.com/watch?v=%s" % (info['entries'][0]['id'])
        response = "".join([
            i if ord(i) < 128 else ' '
            for i in response
        ])
    else:
        response = "No video found, " + gender_prefix + "."
    data = {}
    data['response'] = response
    data['url'] = url
    return json.dumps(data, indent=4)


@hug.post('/notification', requires=token_authentication)
def notification(user_id, location, gender_prefix):
    """**Endpoint** to serve the **notifications** from the **database**.

    Args:
        user_id (int):          User's ID.
        location (str):         *Development in progress...*
        gender_prefix (str):    Prefix to address/call user when answering.

    Returns:
        JSON document.
    """

    url = ""
    title = ""
    message = ""

    db = pymysql.connect(Config.MYSQL_HOST, Config.MYSQL_USER, Config.MYSQL_PASS, Config.MYSQL_DB)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    sql1 = "SELECT * FROM users WHERE id = {}".format(user_id)
    sql2 = "SELECT * FROM notifications"
    try:
        cursor.execute(sql1)
        results = cursor.fetchall()
        if results:
            row = results[0]
            name = row["name"]
            gender = row["gender"]
            birth_date = row["birth_date"]
        else:
            name = "Master"
            gender = 1
            birth_date = "1980-01-01"

        cursor.execute(sql2)
        results = cursor.fetchall()
        row = choice(results)
        if row["capitalize"] == 1:
            gender_prefix = gender_prefix.capitalize()
        url = row["url"]
        title = row["title"]
        message = row["message"].format(gender_prefix, name)
    except pymysql.InternalError as error:
        code, message = error.args
        print (">>>>>>>>>>>>>", code, message)
    db.close()

    data = {}
    data['url'] = url
    data['title'] = title
    data['message'] = message
    return json.dumps(data, indent=4)


# Endpoint to handle registration requests
@hug.post('/register', requires=token_authentication)
def register(name, gender, birth_date):
    """**Endpoint** to handle **registration requests**.

    Args:
        name (str):         User's name.
        gender (str):       User's gender.
        birth_date (str):   User's birth date.

    Returns:
        JSON document.
    """

    id = ""

    db = pymysql.connect(Config.MYSQL_HOST, Config.MYSQL_USER, Config.MYSQL_PASS, Config.MYSQL_DB)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    sql = """
        INSERT INTO users (name, gender, birth_date)
        VALUES('{}', '{}', '{}')
        """.format(name, gender, birth_date)
    try:
        cursor.execute(sql)
        db.commit()
        id = cursor.lastrowid
    except pymysql.InternalError as error:
        code, message = error.args
        print (">>>>>>>>>>>>>", code, message)
    db.close()

    return json.dumps(id, indent=4)


class Run():
    """Class to Run the API.

    .. note::

        Creating an object from this class is automatically starts the API server.

    """

    def __init__(self, nlp_ref, learner_ref, omniscient_ref, dc_ref, userin_ref, token, port_number):
        """Initialization method of :class:`dragonfire.api.Run` class

        This method starts an API server using :mod:`waitress` (*a pure-Python WSGI server*)
        on top of lightweight :mod:`hug` API framework.

        Args:
            nlp_ref:                :mod:`spacy` model instance.
            learner_ref:            :class:`dragonfire.learn.Learner` instance.
            omniscient_ref:         :class:`dragonfire.omniscient.Omniscient` instance.
            dc_ref:                 :class:`dragonfire.conversational.DeepConversation` instance.
            userin_ref:             :class:`dragonfire.utilities.TextToAction` instance.
            token (str):            API token.
            port_number (int):      Port number that the API will be served.
        """

        global nlp
        global learner
        global omniscient
        global dc
        global userin
        global precomptoken
        nlp = nlp_ref  # Load en_core_web_sm, English, 50 MB, default model
        learner = learner_ref
        omniscient = omniscient_ref
        dc = dc_ref
        userin = userin_ref
        precomptoken = token
        app = hug.API(__name__)
        app.http.output_format = hug.output_format.text
        app.http.add_middleware(CORSMiddleware(app))
        t = Thread(target=waitress.serve, args=(__hug_wsgi__, ), kwargs={"port": port_number})
        t.start()
        t.join()


if __name__ == '__main__':
    app = hug.API(__name__)
    app.http.output_format = hug.output_format.text
    app.http.add_middleware(CORSMiddleware(app))
    waitress.serve(__hug_wsgi__, port=8000)
