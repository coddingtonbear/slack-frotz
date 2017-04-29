from flask import Flask, request

from . import config, frotz


app = Flask(__name__)


@app.route("/")
def index():
    return "OK"


@app.route("/play")
def play():
    session_id = request.args['session_id']
    data_id = request.args['data_id']

    command = request.form['text'].strip()

    session = frotz.Session(data_id, session_id)

    try:
        response = session.input(command)
    except frotz.Error:
        pass

    if response:
        pass
