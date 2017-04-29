from flask import Flask, jsonify, request

from . import frotz


app = Flask(__name__)


@app.route("/")
def index():
    return "OK"


@app.route("/play/<data_id>/<session_id>")
def play(data_id, session_id):
    command = request.form['text'].strip()
    if 'trigger_word' in request.form:
        command = command[len(request.form['trigger_word']) + 1:].strip()

    session = frotz.Session(data_id, session_id)

    try:
        state = session.input(command)
    except frotz.Reset:
        return jsonify({
            'title': 'Game Reset',
            'text': 'Your game has been reset.',
        })
    except frotz.Error as e:
        return jsonify({
            'title': 'Frotz Error',
            'text': unicode(e)
        })
    except Exception as e:
        return jsonify({
            'title': 'Exception',
            'text': unicode(e)
        })

    return jsonify({
        'title': state['title'],
        'text': state['message'],
    })
